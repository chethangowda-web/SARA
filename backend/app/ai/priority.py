import re
from typing import List
from app.ai.base import PriorityAssessorProvider, PriorityResult

class DeterministicPriorityAssessor(PriorityAssessorProvider):
    """
    Auditable, deterministic signal-based priority scoring engine.
    Calculates priority strictly from factual evidence signals extracted from the complaint text.
    Does NOT make accusations or disciplinary judgments.
    """

    def assess_priority(
        self, title: str, description: str, location: str, category: str
    ) -> PriorityResult:
        full_text = f"{title} {description} {location}".lower()
        signals: List[str] = []
        score = 10 # Base score for any submitted grievance

        # 1. Category Base Weight
        if category == "ELECTRICAL_SAFETY":
            score += 20
            signals.append("category:electrical_safety")
        elif category in ["PUBLIC_HEALTH", "WATER_SUPPLY", "SANITATION"]:
            score += 10
            signals.append(f"category:{category.lower()}")

        # 2. Electrical & Fire Hazard Signal
        if any(w in full_text for w in ["wire", "electric", "spark", "transformer", "live wire", "high voltage", "current", "fire"]):
            score += 35
            signals.append("electrical_fire_hazard")

        # 3. Danger to Life Signal
        if any(w in full_text for w in ["danger", "death", "fatal", "injury", "collapse", "electrocution", "killing", "life risk", "exposed"]):
            score += 35
            signals.append("danger_to_life")

        # 4. School, Hospital, Vulnerable Context Signal
        if any(w in full_text for w in ["school", "hospital", "kindergarten", "nursery", "college", "clinic", "dispensary"]):
            score += 25
            signals.append("school_hospital_context")

        # 5. Children & Vulnerable Population Signal
        if any(w in full_text for w in ["children", "child", "kids", "students", "infant", "toddler", "patients"]):
            score += 20
            signals.append("children_vulnerable_exposed")

        # 6. Public Health & Sanitation Hazard Signal
        if any(w in full_text for w in ["contamination", "dengue", "sewage overflow", "biohazard", "toxic"]):
            score += 15
            signals.append("public_health_sanitation_risk")

        # 7. Duration / Urgency Signal
        if any(w in full_text for w in ["yesterday", "days", "weeks", "since", "unresolved", "ongoing", "long time"]):
            score += 10
            signals.append("duration_reported_since_yesterday")

        # Cap score between 0 and 100
        final_score = min(100, max(0, score))

        # Assign priority tier
        if final_score >= 75:
            priority = "CRITICAL"
        elif final_score >= 55:
            priority = "HIGH"
        elif final_score >= 35:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        # Generate factual explanation
        if signals:
            explanation = f"Priority scored at {final_score}/100 ({priority}) based on identified factual risk signals: {', '.join(signals)}."
        else:
            explanation = f"Priority scored at {final_score}/100 ({priority}) based on standard non-emergency baseline criteria."

        return PriorityResult(
            priority=priority,
            priority_score=final_score,
            signals=signals,
            explanation=explanation
        )
