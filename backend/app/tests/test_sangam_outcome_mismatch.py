import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.models.grievance import Grievance
from app.sangam.models import GovernmentProject
from app.sangam.services.clustering_service import NeedClusteringService
from app.sangam.services.investment_service import InvestmentService
from app.sangam.services.gap_detection_service import GapDetectionService

@pytest.mark.asyncio
async def test_outcome_mismatch_detection_scenario(db_session, test_citizen):
    # Scenario 2: Completed project exists, but complaints continue -> POTENTIAL_OUTCOME_MISMATCH
    project = GovernmentProject(
        project_code=f"WAT-TEST-{uuid.uuid4()}",
        name="MG Road Water Infrastructure Overhaul",
        description="Comprehensive main line pipeline replacement on MG Road.",
        category="WATER_SUPPLY",
        location="MG Road",
        allocated_amount=5000000.0,
        spent_amount=4800000.0,
        status="COMPLETED",
        source="TEST"
    )
    db_session.add(project)

    for i in range(5):
        g = Grievance(
            citizen_id=test_citizen.id,
            title=f"Water pipe issue after upgrade #{i}",
            description="Dirty water and leakage still continuing on MG Road.",
            category="WATER_SUPPLY",
            location="MG Road",
            current_state="SUBMITTED",
            priority="HIGH"
        )
        db_session.add(g)

    await db_session.commit()

    clustering_service = NeedClusteringService()
    investment_service = InvestmentService()
    gap_service = GapDetectionService()

    await clustering_service.synchronize_need_clusters(db_session)
    await investment_service.match_projects_to_clusters(db_session)
    alerts = await gap_service.analyze_and_generate_alerts(db_session)

    mismatch_alerts = [a for a in alerts if a.type == "POTENTIAL_OUTCOME_MISMATCH" and "MG Road" in a.title]
    assert len(mismatch_alerts) >= 1
    assert mismatch_alerts[0].evidence_json["project_status"] == "COMPLETED"
