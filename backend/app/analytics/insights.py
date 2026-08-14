import json
import re
from datetime import datetime, timezone
from typing import Optional, List
import google.generativeai as genai

from app.core.config import settings
from app.schemas.analytics import GlobalMetricsResponse, DepartmentMetricsResponse, AIInsightResponse

class InsightsGenerator:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)

    def _fallback_insights(self, metrics: str) -> AIInsightResponse:
        """Deterministic rule-based insights generation."""
        insights = [
            "Deterministic observation based on current metrics.",
            "Review anomalies tab for significant deviations.",
            "Monitor SLA compliance trends carefully.",
            f"Metrics summary processed at {datetime.now(timezone.utc).isoformat()}."
        ]
        return AIInsightResponse(
            insights=insights,
            generated_at=datetime.now(timezone.utc),
            provider="DeterministicFallback",
            is_fallback=True
        )

    def generate_insights(self, global_metrics: GlobalMetricsResponse, dept_metrics: List[DepartmentMetricsResponse]) -> AIInsightResponse:
        metrics_data = {
            "global": global_metrics.model_dump(),
            "departments": [d.model_dump(mode='json') for d in dept_metrics]
        }
        metrics_str = json.dumps(metrics_data, default=str)

        if not self.api_key:
            return self._fallback_insights(metrics_str)

        prompt = f"""You are an expert operations analyst. Review the following structured operational metrics and provide 4-5 concise, actionable bullet points describing current trends, risks, and observations. Do not make up facts; use only the provided data.

Metrics:
{metrics_str}

Output the insights strictly in this JSON format:
{{
  "insights": [
    "insight 1",
    "insight 2",
    "insight 3",
    "insight 4"
  ]
}}
"""

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.2, "max_output_tokens": 500},
                request_options={"timeout": float(settings.AI_TIMEOUT_SECONDS)}
            )
            raw_text = response.text.strip()
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                insights = data.get("insights", [])
                if insights:
                    return AIInsightResponse(
                        insights=insights,
                        generated_at=datetime.now(timezone.utc),
                        provider="Gemini-1.5-Flash",
                        is_fallback=False
                    )
        except Exception:
            pass
            
        return self._fallback_insights(metrics_str)
