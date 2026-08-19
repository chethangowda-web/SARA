import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.assignment import Assignment
from app.models.governance import Notification
from app.governance.services import create_in_app_notification
from app.services.assignment_service import auto_route_and_assign, SYSTEM_USER_ID

@pytest_asyncio.fixture(autouse=True)
async def seed_system_user(db_session):
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
async def seed_four_departments_and_staff(db_session):
    hashed_pass = hash_password("password")
    
    # 1. Departments
    dept_codes = {
        "WATER": "Water Supply Department",
        "ELEC": "Electrical Department",
        "ROADS": "Roads & Infrastructure",
        "SANITATION": "Sanitation & Waste"
    }
    depts = {}
    for code, name in dept_codes.items():
        res = await db_session.execute(select(Department).where(Department.code == code))
        d = res.scalars().first()
        if not d:
            d = Department(name=name, code=code, is_active=True)
            db_session.add(d)
        depts[code] = d
    await db_session.commit()
        
    # 2. Staff (Officers & Supervisors)
    officers = {}
    supervisors = {}
    
    for code in dept_codes.keys():
        off = User(
            email=f"{code.lower()}_officer_{uuid.uuid4()}@sara.com",
            full_name=f"{code.capitalize()} Officer",
            password_hash=hashed_pass,
            role=UserRole.OFFICER,
            department_id=depts[code].id,
            is_active=True
        )
        sup = User(
            email=f"{code.lower()}_supervisor_{uuid.uuid4()}@sara.com",
            full_name=f"{code.capitalize()} Supervisor",
            password_hash=hashed_pass,
            role=UserRole.SUPERVISOR,
            department_id=depts[code].id,
            is_active=True
        )
        db_session.add_all([off, sup])
        officers[code] = off
        supervisors[code] = sup
        
    await db_session.commit()
    for k in officers.keys():
        await db_session.refresh(officers[k])
        await db_session.refresh(supervisors[k])
        
    return {"depts": depts, "officers": officers, "supervisors": supervisors}

@pytest_asyncio.fixture
async def test_citizen_user(db_session):
    citizen = User(
        email=f"e2e_citizen_{uuid.uuid4()}@sara.com",
        full_name="E2E Verification Citizen",
        password_hash=hash_password("password"),
        role=UserRole.CITIZEN,
        preferred_language="en",
        is_active=True
    )
    db_session.add(citizen)
    await db_session.commit()
    await db_session.refresh(citizen)
    return citizen

# -----------------------------------------------------------------------------
# 1. Multi-Department Routing Atomic Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_routing_kannada_water(db_session, seed_four_departments_and_staff, test_citizen_user):
    token = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    with patch('app.ai.pipeline.detect_language', return_value='kn'), \
         patch('app.ai.pipeline.normalize_to_english', return_value=("Water pipe is broken", "Main water pipeline leak")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res_kn = await ac.post(
                f"{settings.API_V1_STR}/grievances",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ", "description": "ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ", "location": "Ward 12"}
            )
        assert res_kn.status_code == 201, f"Kannada post failed: {res_kn.text}"
        data_kn = res_kn.json()
        assert data_kn["original_language"] == "kn"
        assert data_kn["original_title"] == "ನೀರಿನ ಪೈಪ್ ಒಡೆದಿದೆ"
        assert data_kn["normalized_title"] == "Water pipe is broken"
        assert data_kn["category"] == "WATER_SUPPLY"
        assert data_kn["department_id"] == str(seed_four_departments_and_staff["depts"]["WATER"].id)
        assert data_kn["assigned_officer_id"] == str(seed_four_departments_and_staff["officers"]["WATER"].id)
        assert data_kn["current_state"] == "ASSIGNED"

@pytest.mark.asyncio
async def test_e2e_routing_hindi_elec(db_session, seed_four_departments_and_staff, test_citizen_user):
    token = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    with patch('app.ai.pipeline.detect_language', return_value='hi'), \
         patch('app.ai.pipeline.normalize_to_english', return_value=("Street light is broken", "Street light fuse blown street lighting pole power electrical bulb outage")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res_hi = await ac.post(
                f"{settings.API_V1_STR}/grievances",
                headers={"Authorization": f"Bearer {token}"},
                json={"title": "स्ट्रीट लाइट खराब है", "description": "स्ट्रीट लाइट खराब है", "location": "Ward 5"}
            )
        assert res_hi.status_code == 201, f"Hindi post failed: {res_hi.text}"
        data_hi = res_hi.json()
        assert data_hi["original_language"] == "hi"
        assert data_hi["normalized_title"] == "Street light is broken"
        assert data_hi["category"] in ["STREET_LIGHTING", "ELECTRICAL_SAFETY"]
        assert data_hi["department_id"] == str(seed_four_departments_and_staff["depts"]["ELEC"].id)
        assert data_hi["assigned_officer_id"] == str(seed_four_departments_and_staff["officers"]["ELEC"].id)
        assert data_hi["current_state"] == "ASSIGNED"

@pytest.mark.asyncio
async def test_e2e_routing_roads(db_session, seed_four_departments_and_staff, test_citizen_user):
    token = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_roads = await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Pothole on 5th main road", "description": "Large road damage pothole asphalt tar street crater", "location": "5th Main"}
        )
    assert res_roads.status_code == 201, f"Roads post failed: {res_roads.text}"
    data_roads = res_roads.json()
    assert data_roads["category"] in ["ROAD_INFRASTRUCTURE", "ROAD_DAMAGE"]
    assert data_roads["department_id"] == str(seed_four_departments_and_staff["depts"]["ROADS"].id)

@pytest.mark.asyncio
async def test_e2e_routing_sanitation(db_session, seed_four_departments_and_staff, test_citizen_user):
    token = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_san = await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Garbage dump overflow", "description": "Garbage dump overflow trash uncollected solid waste garbage bin street sanitation", "location": "Market Yard"}
        )
    assert res_san.status_code == 201, f"Sanitation post failed: {res_san.text}"
    data_san = res_san.json()
    assert data_san["category"] == "SANITATION"
    assert data_san["department_id"] == str(seed_four_departments_and_staff["depts"]["SANITATION"].id)


# -----------------------------------------------------------------------------
# 2. Workload Optimizer & Audit Snapshot Verification
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_workload_optimizer_snapshot(db_session, seed_four_departments_and_staff, test_citizen_user):
    water_dept = seed_four_departments_and_staff["depts"]["WATER"]
    
    # Create Officer A and Officer B in WATER department
    officer_a = User(
        email=f"officer_a_{uuid.uuid4()}@sara.com",
        full_name="Water Officer A",
        password_hash=hash_password("pass"),
        role=UserRole.OFFICER,
        department_id=water_dept.id,
        is_active=True
    )
    officer_b = User(
        email=f"officer_b_{uuid.uuid4()}@sara.com",
        full_name="Water Officer B",
        password_hash=hash_password("pass"),
        role=UserRole.OFFICER,
        department_id=water_dept.id,
        is_active=True
    )
    db_session.add_all([officer_a, officer_b])
    await db_session.commit()

    # Ensure default water officer has 10 cases so Officer B (1 case) is lowest
    default_water_off = seed_four_departments_and_staff["officers"]["WATER"]
    for i in range(10):
        g = Grievance(
            citizen_id=test_citizen_user.id,
            title=f"Water case default {i}",
            description="Water leak",
            location="Loc Def",
            current_state="ASSIGNED",
            department_id=water_dept.id,
            assigned_officer_id=default_water_off.id
        )
        db_session.add(g)
        await db_session.commit()
        db_session.add(Assignment(grievance_id=g.id, officer_id=default_water_off.id, is_active=True))
        await db_session.commit()

    # Assign 5 active cases to Officer A, 0 active cases to Officer B
    for i in range(5):
        g = Grievance(
            citizen_id=test_citizen_user.id,
            title=f"Water case A {i}",
            description="Water leak",
            location="Loc A",
            current_state="ASSIGNED",
            department_id=water_dept.id,
            assigned_officer_id=officer_a.id
        )
        db_session.add(g)
        await db_session.commit()
        db_session.add(Assignment(grievance_id=g.id, officer_id=officer_a.id, is_active=True))
        await db_session.commit()

    # Submit a new water grievance
    token = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "Water contamination", "description": "Water contamination dirty water supply main pipe", "location": "Block 9"}
        )
    assert res.status_code == 201
    data = res.json()
    
    # Must be assigned to Officer B (lowest workload: 0 active cases)
    assert data["assigned_officer_id"] == str(officer_b.id)
    
    # Inspect Assignment record in DB
    g_id = uuid.UUID(data["id"])
    res_a = await db_session.execute(select(Assignment).where(Assignment.grievance_id == g_id, Assignment.is_active == True))
    active_assignment = res_a.scalars().first()
    
    assert active_assignment is not None
    assert active_assignment.reason == "Auto-assigned by SARA Workload Optimizer"
    assert active_assignment.workload_snapshot is not None
    
    snapshot = active_assignment.workload_snapshot
    assert str(officer_a.id) in snapshot
    assert str(officer_b.id) in snapshot
    assert snapshot[str(officer_a.id)]["active"] == 5
    assert snapshot[str(officer_b.id)]["active"] == 0


# -----------------------------------------------------------------------------
# 3. Officer Start Work API & State Machine
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_officer_start_work_transitions(db_session, seed_four_departments_and_staff, test_citizen_user):
    water_off = seed_four_departments_and_staff["officers"]["WATER"]
    water_dept = seed_four_departments_and_staff["depts"]["WATER"]
    
    # Create an assigned grievance
    g = Grievance(
        citizen_id=test_citizen_user.id,
        title="Pipe burst test start work",
        description="Water pipe burst leak",
        location="Loc 3",
        current_state="ASSIGNED",
        department_id=water_dept.id,
        assigned_officer_id=water_off.id
    )
    db_session.add(g)
    await db_session.commit()
    db_session.add(Assignment(grievance_id=g.id, officer_id=water_off.id, is_active=True))
    await db_session.commit()

    token_off = create_access_token(water_off.id, water_off.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Acknowledge: ASSIGNED -> ACKNOWLEDGED
        res_ack = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/acknowledge",
            headers={"Authorization": f"Bearer {token_off}"}
        )
        assert res_ack.status_code == 200, f"Acknowledge failed: {res_ack.text}"
        assert res_ack.json()["current_state"] == "ACKNOWLEDGED"

        # Start Work: ACKNOWLEDGED -> IN_PROGRESS
        res_start = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/start",
            headers={"Authorization": f"Bearer {token_off}"}
        )
        assert res_start.status_code == 200, f"Start work failed: {res_start.text}"
        assert res_start.json()["current_state"] == "IN_PROGRESS"

    # Verify DB state updated
    await db_session.refresh(g)
    assert g.current_state == "IN_PROGRESS"


# -----------------------------------------------------------------------------
# 4. Complete Lifecycle (Success Path & Rejection Path)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_complete_lifecycles(db_session, seed_four_departments_and_staff, test_citizen_user):
    water_off = seed_four_departments_and_staff["officers"]["WATER"]
    water_sup = seed_four_departments_and_staff["supervisors"]["WATER"]
    water_dept = seed_four_departments_and_staff["depts"]["WATER"]
    
    token_cit = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    token_off = create_access_token(water_off.id, water_off.role.value)
    token_sup = create_access_token(water_sup.id, water_sup.role.value)

    # --- PATH A: Full Success -> CLOSED ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        g_id = (await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token_cit}"},
            json={"title": "Water pipe leak full path", "description": "Water leak drinking water supply main pipe", "location": "Loc 4"}
        )).json()["id"]

        await ac.post(f"{settings.API_V1_STR}/grievances/{g_id}/acknowledge", headers={"Authorization": f"Bearer {token_off}"})
        await ac.post(f"{settings.API_V1_STR}/grievances/{g_id}/start", headers={"Authorization": f"Bearer {token_off}"})
        
        # Submit Resolution -> RESOLUTION_SUBMITTED
        res_res = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g_id}/resolve",
            headers={"Authorization": f"Bearer {token_off}"},
            json={"resolution_notes": "Replaced burst pipe joint and restored water pressure"}
        )
        assert res_res.status_code == 200, f"Resolve failed: {res_res.text}"
        assert res_res.json()["current_state"] == "RESOLUTION_SUBMITTED"

        # Supervisor Review APPROVE -> VERIFICATION
        res_rev = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g_id}/review",
            headers={"Authorization": f"Bearer {token_sup}"},
            json={"action": "APPROVE"}
        )
        assert res_rev.status_code == 200, f"Supervisor review failed: {res_rev.text}"
        assert res_rev.json()["current_state"] == "VERIFICATION"

        # Citizen Verify ACCEPT -> CLOSED
        res_ver = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g_id}/verify",
            headers={"Authorization": f"Bearer {token_cit}"},
            json={"action": "ACCEPT"}
        )
        assert res_ver.status_code == 200, f"Citizen verify failed: {res_ver.text}"
        assert res_ver.json()["current_state"] == "CLOSED"

    # --- PATH B: Citizen Rejection -> REOPENED ---
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        g2_id = (await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token_cit}"},
            json={"title": "Water pipe leak rejection path", "description": "Water leak drinking water supply main pipe", "location": "Loc 5"}
        )).json()["id"]

        await ac.post(f"{settings.API_V1_STR}/grievances/{g2_id}/acknowledge", headers={"Authorization": f"Bearer {token_off}"})
        await ac.post(f"{settings.API_V1_STR}/grievances/{g2_id}/start", headers={"Authorization": f"Bearer {token_off}"})
        await ac.post(f"{settings.API_V1_STR}/grievances/{g2_id}/resolve", headers={"Authorization": f"Bearer {token_off}"}, json={"resolution_notes": "Patched pipe"})
        await ac.post(f"{settings.API_V1_STR}/grievances/{g2_id}/review", headers={"Authorization": f"Bearer {token_sup}"}, json={"action": "APPROVE"})

        # Citizen Verify REJECT -> REOPENED
        res_rej = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g2_id}/verify",
            headers={"Authorization": f"Bearer {token_cit}"},
            json={"action": "REJECT", "reason": "Water is still leaking onto the road"}
        )
        assert res_rej.status_code == 200, f"Citizen reject failed: {res_rej.text}"
        assert res_rej.json()["current_state"] == "REOPENED"


# -----------------------------------------------------------------------------
# 5. Low-Confidence Exclusion Path
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_low_confidence_exclusion(db_session, test_citizen_user):
    token_cit = create_access_token(test_citizen_user.id, test_citizen_user.role.value)
    
    from app.ai.base import ClassificationResult
    low_result = ClassificationResult(category="OTHER", confidence=0.50, provider="TFIDF")

    with patch('app.ai.pipeline.classifier.classify', return_value=low_result):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.post(
                f"{settings.API_V1_STR}/grievances",
                headers={"Authorization": f"Bearer {token_cit}"},
                json={"title": "hello world", "description": "hello world ambiguity test", "location": "Unknown"}
            )
        assert res.status_code == 201, f"Low conf post failed: {res.text}"
        data = res.json()
        
        assert data["current_state"] == "CLASSIFIED"
        assert data["category"] == "OTHER"
        assert data["department_id"] is None
        assert data["assigned_officer_id"] is None


# -----------------------------------------------------------------------------
# 6. Multilingual Notification Translation
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_e2e_multilingual_notifications(db_session, test_citizen_user):
    test_citizen_user.preferred_language = "kn"
    db_session.add(test_citizen_user)
    await db_session.commit()

    notif = await create_in_app_notification(
        db=db_session,
        user_id=test_citizen_user.id,
        grievance_id=None,
        title="Resolution Submitted",
        message="A resolution for grievance test has been submitted and is awaiting department supervisor review.",
        notification_type="RESOLUTION_SUBMITTED"
    )
    await db_session.commit()

    assert "ಪರಿಹಾರವನ್ನು ಸಲ್ಲಿಸಲಾಗಿದೆ" in notif.title
    assert "ಸಲ್ಲಿಸಲಾಗಿದೆ" in notif.message
