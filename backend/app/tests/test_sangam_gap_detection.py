import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.models.grievance import Grievance
from app.models.user import UserRole
from app.core.security import create_access_token
from app.sangam.services.gap_detection_service import GapDetectionService
from app.sangam.services.clustering_service import NeedClusteringService

@pytest.mark.asyncio
async def test_unserved_gap_detection_scenario(db_session, test_admin, test_citizen):
    # Scenario 1: 100 water complaints + no matching project -> UNSERVED_GAP alert
    for i in range(10):  # Using 10 representative grievances for speed
        g = Grievance(
            citizen_id=test_citizen.id,
            title=f"Water Pipeline Leakage #{i}",
            description="Severe water supply disruption and main pipe rupture near market area.",
            category="WATER_SUPPLY",
            location="Whitefield Market",
            current_state="SUBMITTED",
            priority="HIGH"
        )
        db_session.add(g)

    await db_session.commit()

    clustering_service = NeedClusteringService()
    gap_service = GapDetectionService()

    await clustering_service.synchronize_need_clusters(db_session)
    alerts = await gap_service.analyze_and_generate_alerts(db_session)

    unserved_gap_alerts = [a for a in alerts if a.type == "UNSERVED_GAP"]
    assert len(unserved_gap_alerts) >= 1
    assert "Whitefield Market" in unserved_gap_alerts[0].description or "Whitefield Market" in unserved_gap_alerts[0].title
    assert unserved_gap_alerts[0].evidence_json["matching_projects_count"] == 0
