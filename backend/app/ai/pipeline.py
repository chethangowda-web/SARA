import uuid
import re
import json
from typing import Dict, Any, Tuple, Optional
import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.models.grievance import Grievance
from app.models.grievance_embedding import GrievanceEmbedding
from app.ai.classifier import MLClassifier
from app.ai.priority import DeterministicPriorityAssessor
from app.ai.summarizer import GeminiSummarizer
from app.ai.embeddings import FastEmbedProvider
from app.ai.duplicate_detector import VectorDuplicateDetector
from app.services.grievance_service import transition_grievance
from app.core.config import settings

# Singleton instances of AI engines
classifier = MLClassifier()
priority_assessor = DeterministicPriorityAssessor()
summarizer = GeminiSummarizer()
embedding_provider = FastEmbedProvider()
duplicate_detector = VectorDuplicateDetector()

def detect_language(title: str, description: str, api_key: Optional[str] = None) -> str:
    """Detect language of the text. Fall back to 'kn' if non-ASCII is found, otherwise 'en'."""
    text = f"{title} {description}"
    has_non_ascii = any(ord(c) > 127 for c in text)
    
    if not api_key:
        return "kn" if has_non_ascii else "en"
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""Analyze the language of the following text. Respond with ONLY the ISO 639-1 language code (e.g., 'en', 'kn', 'hi', 'te', 'ta', 'ml', 'mr', 'bn', etc.). Do not include punctuation or other words.
        
        Text: {text[:500]}"""
        response = model.generate_content(prompt, generation_config={"temperature": 0.0, "max_output_tokens": 10})
        lang_code = response.text.strip().lower()
        match = re.search(r"\b[a-z]{2}\b", lang_code)
        if match:
            return match.group(0)
        return "en" if "en" in lang_code else "kn"
    except Exception:
        return "kn" if has_non_ascii else "en"

def normalize_to_english(title: str, description: str, api_key: Optional[str] = None) -> Tuple[str, str]:
    """Translate title and description to English. Return original text as fallback."""
    if not api_key:
        return title, description
        
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""You are a translation assistant. Translate the following title and description of a citizen grievance to English. Keep the tone formal and preserve all key facts. Respond ONLY with a JSON object matching this schema:
        {{
          "title": "Translated Title",
          "description": "Translated Description"
        }}
        
        Title: {title}
        Description: {description}"""
        response = model.generate_content(prompt, generation_config={"temperature": 0.1, "max_output_tokens": 1000})
        raw_text = response.text.strip()
        match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("title", title), data.get("description", description)
    except Exception:
        pass
    return title, description

async def process_grievance_ai_pipeline(db: AsyncSession, grievance_id: uuid.UUID) -> Grievance:
    """
    Orchestrates the AI advisory pipeline for a newly submitted grievance:
    1. Language Detection & Preservation
    2. Normalization (Translation) to English
    3. Classification (TF-IDF on normalized English text)
    4. Priority Assessment (on normalized English text)
    5. Summarization (on normalized English text)
    6. Embedding Generation & Vector Storage (on normalized English text)
    7. Advisory Duplicate Detection (on normalized English text)
    8. Centralized State Machine Transition (SUBMITTED -> CLASSIFIED)
    9. Automated Route & Workload-Aware Assignment
    """
    result = await db.execute(select(Grievance).where(Grievance.id == grievance_id))
    grievance = result.scalars().first()
    if not grievance:
        raise ValueError(f"Grievance {grievance_id} not found")

    # Retrieve Gemini API Key safely
    api_key = settings.GEMINI_API_KEY if settings.GEMINI_API_KEY and "your_gemini_api_key" not in settings.GEMINI_API_KEY else None

    # 1. Language Detection & Preservation
    detected_lang = detect_language(grievance.title, grievance.description, api_key)
    grievance.original_language = detected_lang
    grievance.original_title = grievance.title
    grievance.original_description = grievance.description

    # 2. Normalization (Translation) to English
    if detected_lang != "en":
        norm_title, norm_desc = normalize_to_english(grievance.title, grievance.description, api_key)
        grievance.normalized_title = norm_title
        grievance.normalized_description = norm_desc
    else:
        norm_title = grievance.title
        norm_desc = grievance.description
        grievance.normalized_title = grievance.title
        grievance.normalized_description = grievance.description

    # Auto-update citizen's language preferences if set to English and they submitted non-English
    res_citizen = await db.execute(select(User).where(User.id == grievance.citizen_id))
    citizen = res_citizen.scalars().first()
    if citizen and citizen.preferred_language == 'en' and detected_lang != 'en':
        citizen.preferred_language = detected_lang
        await db.flush()

    # Now use normalized English text for all downstream AI engines
    title_for_ai = norm_title
    desc_for_ai = norm_desc
    location = grievance.location

    # 3. Classification
    try:
        class_res = classifier.classify(title_for_ai, desc_for_ai)
    except Exception:
        from app.ai.base import ClassificationResult
        class_res = ClassificationResult(category="General", confidence=0.5, provider="Fallback", is_fallback=True)
    
    # 4. Priority Assessment
    try:
        prio_res = priority_assessor.assess_priority(title_for_ai, desc_for_ai, location, class_res.category)
    except Exception:
        from app.ai.priority import PriorityResult
        prio_res = PriorityResult(
            priority="MEDIUM", 
            priority_score=50, 
            signals=["fallback"], 
            explanation="Priority calculation fallback due to pipeline error"
        )
    
    # 5. Summarization
    try:
        sum_res = summarizer.summarize(title_for_ai, desc_for_ai)
    except Exception:
        from app.ai.base import SummaryResult
        sum_res = SummaryResult(
            summary=f"{title_for_ai}: {desc_for_ai[:100]}...",
            key_facts=[title_for_ai],
            affected_area="Unknown",
            urgency="MEDIUM",
            provider="DeterministicFallback",
            is_fallback=True
        )
    
    # 6. Embeddings
    vec = None
    try:
        text_for_embedding = f"{title_for_ai}. {desc_for_ai}. {location}"
        # Only check user inputs limit
        text_for_embedding = text_for_embedding[:2000]
        vec = embedding_provider.generate_embedding(text_for_embedding)
        
        # Store or update vector in grievance_embeddings table
        res_emb = await db.execute(select(GrievanceEmbedding).where(GrievanceEmbedding.grievance_id == grievance.id))
        existing_emb = res_emb.scalars().first()
        if existing_emb:
            existing_emb.embedding = vec
        else:
            emb_record = GrievanceEmbedding(
                grievance_id=grievance.id,
                embedding=vec,
                model_name="BAAI/bge-small-en-v1.5"
            )
            db.add(emb_record)
        await db.flush()
    except Exception:
        # Fallback to zero vector of size 384
        vec = [0.0] * 384
    
    # 7. Duplicate Detection
    try:
        dup_res = await duplicate_detector.find_duplicates(db, grievance.id, vec)
        dup_info = dup_res.model_dump()
    except Exception:
        dup_info = {"is_duplicate": False, "potential_duplicates": []}

    # Apply AI Advisory Signals onto Grievance Entity
    grievance.category = class_res.category
    grievance.classification_confidence = class_res.confidence
    grievance.priority = prio_res.priority
    grievance.priority_score = prio_res.priority_score
    grievance.priority_signals = {"signals": prio_res.signals}
    grievance.priority_explanation = prio_res.explanation
    grievance.summary = sum_res.summary
    grievance.duplicate_info = dup_info

    await db.flush()

    from app.services.assignment_service import get_system_user
    system_user = await get_system_user(db)
    
    payload = {
        "category": class_res.category,
        "priority": prio_res.priority,
        "confidence": class_res.confidence,
        "summary": sum_res.summary
    }

    updated_grievance = await transition_grievance(
        db=db,
        grievance_id=grievance.id,
        target_state="CLASSIFIED",
        actor=system_user,
        payload=payload
    )

    # 9. Auto-route and auto-assign
    from app.services.assignment_service import auto_route_and_assign
    return await auto_route_and_assign(db, updated_grievance)
