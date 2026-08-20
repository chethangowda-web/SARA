import uuid
from typing import Dict, Any
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

# Singleton instances of AI engines
classifier = MLClassifier()
priority_assessor = DeterministicPriorityAssessor()
summarizer = GeminiSummarizer()
embedding_provider = FastEmbedProvider()
duplicate_detector = VectorDuplicateDetector()

async def process_grievance_ai_pipeline(db: AsyncSession, grievance_id: uuid.UUID) -> Grievance:
    """
    Orchestrates the AI advisory pipeline for a newly submitted grievance:
    1. Classification
    2. Priority Assessment
    3. Summarization
    4. Embedding Generation & Vector Storage
    5. Advisory Duplicate Detection
    6. Centralized State Machine Transition (SUBMITTED -> CLASSIFIED)
    """
    result = await db.execute(select(Grievance).where(Grievance.id == grievance_id))
    grievance = result.scalars().first()
    if not grievance:
        raise ValueError(f"Grievance {grievance_id} not found")

    title = grievance.title
    desc = grievance.description
    location = grievance.location

    # 1. Classification
    try:
        class_res = classifier.classify(title, desc)
    except Exception:
        from app.ai.base import ClassificationResult
        class_res = ClassificationResult(category="General", confidence=0.5, provider="Fallback", is_fallback=True)
    
    # 2. Priority Assessment
    try:
        prio_res = priority_assessor.assess_priority(title, desc, location, class_res.category)
    except Exception:
        from app.ai.priority import PriorityResult
        prio_res = PriorityResult(
            priority="MEDIUM", 
            priority_score=50, 
            signals=["fallback"], 
            explanation="Priority calculation fallback due to pipeline error"
        )
    
    # 3. Summarization
    try:
        sum_res = summarizer.summarize(title, desc)
    except Exception:
        from app.ai.base import SummaryResult
        sum_res = SummaryResult(
            summary=f"{title}: {desc[:100]}...",
            key_facts=[title],
            affected_area="Unknown",
            urgency="MEDIUM",
            provider="DeterministicFallback",
            is_fallback=True
        )
    
    # 4. Embeddings
    vec = None
    try:
        text_for_embedding = f"{title}. {desc}. {location}"
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
    
    # 5. Duplicate Detection
    try:
        dup_res = await duplicate_detector.find_duplicates(db, grievance.id, vec)
        dup_info = dup_res.model_dump()
    except Exception:
        dup_info = {"is_duplicate": False, "potential_duplicates": []}

    # 6. Apply AI Advisory Signals onto Grievance Entity
    grievance.category = class_res.category
    grievance.classification_confidence = class_res.confidence
    grievance.priority = prio_res.priority
    grievance.priority_score = prio_res.priority_score
    grievance.priority_signals = {"signals": prio_res.signals}
    grievance.priority_explanation = prio_res.explanation
    grievance.summary = sum_res.summary
    grievance.duplicate_info = dup_info

    await db.flush()

    # 7. Transition via Centralized State Machine to CLASSIFIED
    system_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        email="ai_system@sara.gov",
        full_name="SARA AI Pipeline System",
        password_hash="",
        role=UserRole.ADMIN,
        is_active=True
    )
    
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

    res = await db.execute(
        select(Grievance)
        .where(Grievance.id == grievance.id)
        .options(selectinload(Grievance.citizen), selectinload(Grievance.department))
    )
    return res.scalars().first()
