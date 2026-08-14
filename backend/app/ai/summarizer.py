import os
import re
import json
import asyncio
from typing import Optional
import google.generativeai as genai

from app.core.config import settings
from app.ai.base import SummarizerProvider, SummaryResult

class GeminiSummarizer(SummarizerProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _sanitize_input(self, text: str) -> str:
        """Sanitize untrusted user input to prevent prompt injection."""
        text = text[:1500]  # Truncate large input
        # Neutralize system prompt override keywords
        text = re.sub(r"(?i)(ignore previous instructions|system prompt|you are now|override)", "[sanitized]", text)
        return text.strip()

    def _fallback_summary(self, title: str, description: str) -> SummaryResult:
        """Deterministic fallback summarizer used when external API is unavailable or times out."""
        sentences = [s.strip() for s in re.split(r"[.!?]", description) if len(s.strip()) > 5]
        first_two = ". ".join(sentences[:2]) if sentences else description[:150]
        
        return SummaryResult(
            summary=f"{title}: {first_two}.",
            key_facts=[title, f"Details provided: {description[:80]}..."],
            affected_area="Specified in complaint location details",
            urgency="STANDARD",
            provider="DeterministicFallback",
            is_fallback=True
        )

    def summarize(self, title: str, description: str) -> SummaryResult:
        clean_title = self._sanitize_input(title)
        clean_desc = self._sanitize_input(description)

        if not self.api_key:
            return self._fallback_summary(clean_title, clean_desc)

        prompt = f"""You are a grievance summarization AI assistant. Summarize the following citizen grievance strictly into JSON format.

Title: {clean_title}
Description: {clean_desc}

JSON Schema required:
{{
  "summary": "1-2 sentence objective overview",
  "key_facts": ["fact 1", "fact 2"],
  "affected_area": "location or area affected",
  "urgency": "CRITICAL / HIGH / MEDIUM / LOW"
}}

Respond ONLY with valid JSON."""

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 300},
                request_options={"timeout": float(settings.AI_TIMEOUT_SECONDS)}
            )
            
            raw_text = response.text.strip()
            # Extract JSON substring
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return SummaryResult(
                    summary=data.get("summary", f"{clean_title}: {clean_desc[:100]}"),
                    key_facts=data.get("key_facts", [clean_title]),
                    affected_area=data.get("affected_area", "Unspecified"),
                    urgency=data.get("urgency", "MEDIUM"),
                    provider="Gemini-1.5-Flash",
                    is_fallback=False
                )
        except Exception:
            pass  # Fall through to deterministic fallback on any exception or timeout

        return self._fallback_summary(clean_title, clean_desc)
