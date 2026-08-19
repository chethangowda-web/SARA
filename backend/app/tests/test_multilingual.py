import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.governance import Notification
from app.governance.services import create_in_app_notification
from app.services.assignment_service import auto_route_and_assign, select_best_officer

@pytest_asyncio.fixture(autouse=True)
async def seed_system_user(db_session):
    from app.services.assignment_service import SYSTEM_USER_ID
    res = await db_session.execute(select(User).where(User.id == SYSTEM_USER_ID))
    sys_user = res.scalars().first()
    if not sys_user:
        sys_user = User(
            id=SYSTEM_USER_ID,
            email="ai_system@sara.gov",
            full_name="SARA AI Pipeline System",
            password_hash="",
            role=UserRole.ADMIN,
            is_active=True
        )
        db_session.add(sys_user)
        await db_session.commit()

@pytest_asyncio.fixture
async def test_departments(db_session):
    # Ensure ELEC and WATER departments exist
    res_elec = await db_session.execute(select(Department).where(Department.code == "ELEC"))
    elec = res_elec.scalars().first()
    if not elec:
        elec = Department(name="Electrical Department", code="ELEC", is_active=True)
        db_session.add(elec)
        
    res_water = await db_session.execute(select(Department).where(Department.code == "WATER"))
    water = res_water.scalars().first()
    if not water:
        water = Department(name="Water Supply Department", code="WATER", is_active=True)
        db_session.add(water)
        
    await db_session.commit()
    return {"ELEC": elec, "WATER": water}

@pytest_asyncio.fixture
async def test_staff(db_session, test_departments):
    hashed_pass = hash_password("password")
    
    # Seed 2 Water Officers for workload testing
    wo1 = User(
        email="water1@sara.com",
        full_name="Water Officer One",
        password_hash=hashed_pass,
        role=UserRole.OFFICER,
        department_id=test_departments["WATER"].id,
        is_active=True
    )
    wo2 = User(
        email="water2@sara.com",
        full_name="Water Officer Two",
        password_hash=hashed_pass,
        role=UserRole.OFFICER,
        department_id=test_departments["WATER"].id,
        is_active=True
    )
    
    # Seed 1 Electrical Officer
    eo = User(
        email="elec@sara.com",
        full_name="Electrical Officer",
        password_hash=hashed_pass,
        role=UserRole.OFFICER,
        department_id=test_departments["ELEC"].id,
        is_active=True
    )
    
    db_session.add_all([wo1, wo2, eo])
    await db_session.commit()
    await db_session.refresh(wo1)
    await db_session.refresh(wo2)
    await db_session.refresh(eo)
    return {"wo1": wo1, "wo2": wo2, "eo": eo}

@pytest.mark.asyncio
async def test_workload_aware_officer_assignment(db_session, test_departments, test_staff, test_citizen):
    # Give wo1 two active assignments
    g_dummy1 = Grievance(
        citizen_id=test_citizen.id,
        title="Dummy 1",
        description="Dummy water issue 1",
        location="Loc 1",
        current_state="ASSIGNED",
        department_id=test_departments["WATER"].id,
        assigned_officer_id=test_staff["wo1"].id
    )
    g_dummy2 = Grievance(
        citizen_id=test_citizen.id,
        title="Dummy 2",
        description="Dummy water issue 2",
        location="Loc 2",
        current_state="ASSIGNED",
        department_id=test_departments["WATER"].id,
        assigned_officer_id=test_staff["wo1"].id
    )
    db_session.add_all([g_dummy1, g_dummy2])
    await db_session.commit()
    
    assign1 = Assignment(grievance_id=g_dummy1.id, officer_id=test_staff["wo1"].id, is_active=True)
    assign2 = Assignment(grievance_id=g_dummy2.id, officer_id=test_staff["wo1"].id, is_active=True)
    db_session.add_all([assign1, assign2])
    await db_session.commit()

    # Now select best officer for WATER department
    best_officer = await select_best_officer(db_session, test_departments["WATER"].id)
    # Water Officer Two (wo2) must be selected because he has 0 active workload compared to wo1's 2
    assert best_officer.id == test_staff["wo2"].id

@pytest.mark.asyncio
async def test_kannada_voice_complaint_flow(db_session, test_departments, test_staff, test_citizen):
    token = create_access_token(test_citizen.id, test_citizen.role.value)
    
    # Mock Gemini language detection to Kannada, and translation to English Water Leakage
    with patch('app.ai.pipeline.detect_language', return_value='kn'), \
         patch('app.ai.pipeline.normalize_to_english', return_value=("Water leakage in Sector 4", "Main pipeline burst and leaking water")):
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                f"{settings.API_V1_STR}/grievances",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "title": "ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ",
                    "description": "ನಮ್ಮ ಏರಿಯಾದಲ್ಲಿ ನೀರಿನ ಪೈಪ್ ಒಡೆದು ಹೋಗಿದೆ.",
                    "location": "Sector 4 Main Road"
                }
            )
            
        assert response.status_code == 201
        data = response.json()
        
        # Original language text must be preserved in main title/description
        assert data["title"] == "ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ"
        assert data["description"] == "ನಮ್ಮ ಏರಿಯಾದಲ್ಲಿ ನೀರಿನ ಪೈಪ್ ಒಡೆದು ಹೋಗಿದೆ." # Submitted description matches
        
        # Multilingual fields populated
        assert data["original_language"] == "kn"
        assert data["original_title"] == "ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ"
        assert data["normalized_title"] == "Water leakage in Sector 4"
        assert data["normalized_description"] == "Main pipeline burst and leaking water"
        
        # Routing outcome checks: WATER_SUPPLY category classified by TF-IDF (since English normalization was processed)
        assert data["category"] == "WATER_SUPPLY"
        assert data["department_name"] == "Water Supply Department"
        assert data["current_state"] == "ASSIGNED"
        assert data["assigned_officer"] in ["Water Officer One", "Water Officer Two"] # Valid officer assigned by workload optimizer
        
        # Validate database assignment history records
        grievance_id = uuid.UUID(data["id"])
        res_assign = await db_session.execute(
            select(Assignment).where(Assignment.grievance_id == grievance_id, Assignment.is_active == True)
        )
        active_assign = res_assign.scalars().first()
        assert active_assign is not None
        assert active_assign.officer_id in [test_staff["wo1"].id, test_staff["wo2"].id]
        assert active_assign.reason == "Auto-assigned by SARA Workload Optimizer"
        assert active_assign.workload_snapshot is not None
        assert str(test_staff["wo2"].id) in active_assign.workload_snapshot
        
        # Citizen preferred language must be auto-updated to kn
        await db_session.refresh(test_citizen)
        assert test_citizen.preferred_language == "kn"

@pytest.mark.asyncio
async def test_confidence_threshold_routing(db_session, test_departments, test_staff, test_citizen):
    token = create_access_token(test_citizen.id, test_citizen.role.value)
    
    # Mock classification to return low confidence (e.g. 0.50)
    from app.ai.base import ClassificationResult
    low_conf_result = ClassificationResult(category="OTHER", confidence=0.50, provider="TFIDF-LogisticRegression")
    
    with patch('app.ai.pipeline.classifier.classify', return_value=low_conf_result):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                f"{settings.API_V1_STR}/grievances",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "title": "Unclear random sentence",
                    "description": "This complaint has no clear civic category context details.",
                    "location": "Unknown Ward"
                }
            )
            
        assert response.status_code == 201
        data = response.json()
        
        # Must stay in CLASSIFIED state and category is OTHER
        assert data["current_state"] == "CLASSIFIED"
        assert data["category"] == "OTHER"
        assert data["department_id"] is None
        assert data["assigned_officer_id"] is None

@pytest.mark.asyncio
async def test_notification_translation_for_kannada_user(db_session, test_citizen):
    # Set citizen language preference to Kannada
    test_citizen.preferred_language = "kn"
    db_session.add(test_citizen)
    await db_session.commit()
    
    # Create notification with English template string
    notif = await create_in_app_notification(
        db=db_session,
        user_id=test_citizen.id,
        grievance_id=None,
        title="Resolution Approved",
        message="The resolution for grievance test has been approved. Please verify the resolution.",
        notification_type="RESOLUTION_APPROVED"
    )
    await db_session.commit()
    
    # Verify notification details are translated
    assert "ಪರಿಹಾರವನ್ನು ಅಂಗೀಕರಿಸಲಾಗಿದೆ" in notif.title
    assert "ಅಂಗೀಕರಿಸಲಾಗಿದೆ" in notif.message
