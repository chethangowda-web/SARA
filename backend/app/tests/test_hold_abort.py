import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.grievance_event import GrievanceEvent
from app.models.assignment import Assignment

# Local helper to create access token headers
def get_auth_headers(user):
    token = create_access_token(str(user.id), user.role.value)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def hold_test_data(db_session):
    # Create Departments
    dept_a = Department(name="Roads Dept", code="ROADS", is_active=True)
    dept_b = Department(name="Water Dept", code="WATER", is_active=True)
    db_session.add_all([dept_a, dept_b])
    await db_session.commit()

    # Create Users
    citizen = User(
        email="citizen_hold@sara.com",
        full_name="Citizen Hold",
        password_hash=hash_password("password"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    officer_a = User(
        email="officer_a_hold@sara.com",
        full_name="Officer A",
        password_hash=hash_password("password"),
        role=UserRole.OFFICER,
        department_id=dept_a.id,
        is_active=True
    )
    officer_b = User(
        email="officer_b_hold@sara.com",
        full_name="Officer B",
        password_hash=hash_password("password"),
        role=UserRole.OFFICER,
        department_id=dept_b.id,
        is_active=True
    )
    supervisor_a = User(
        email="supervisor_a_hold@sara.com",
        full_name="Supervisor A",
        password_hash=hash_password("password"),
        role=UserRole.SUPERVISOR,
        department_id=dept_a.id,
        is_active=True
    )
    supervisor_b = User(
        email="supervisor_b_hold@sara.com",
        full_name="Supervisor B",
        password_hash=hash_password("password"),
        role=UserRole.SUPERVISOR,
        department_id=dept_b.id,
        is_active=True
    )
    db_session.add_all([citizen, officer_a, officer_b, supervisor_a, supervisor_b])
    await db_session.commit()

    # Create Grievance 1 (Roads) and Grievance 2 (Water)
    g1 = Grievance(
        citizen_id=citizen.id,
        department_id=dept_a.id,
        title="Pothole on Main St",
        description="Huge pothole causing traffic issues.",
        location="123 Main St",
        current_state="ASSIGNED",
        assigned_officer_id=officer_a.id,
        submitted_at=datetime.now(timezone.utc)
    )
    g2 = Grievance(
        citizen_id=citizen.id,
        department_id=dept_b.id,
        title="Water leak on 2nd Ave",
        description="Water gushing out of pipeline.",
        location="456 2nd Ave",
        current_state="ASSIGNED",
        assigned_officer_id=officer_b.id,
        submitted_at=datetime.now(timezone.utc)
    )
    db_session.add_all([g1, g2])
    await db_session.commit()

    # Active assignments
    assign1 = Assignment(
        grievance_id=g1.id,
        officer_id=officer_a.id,
        is_active=True,
        assigned_at=datetime.now(timezone.utc)
    )
    assign2 = Assignment(
        grievance_id=g2.id,
        officer_id=officer_b.id,
        is_active=True,
        assigned_at=datetime.now(timezone.utc)
    )
    db_session.add_all([assign1, assign2])
    await db_session.commit()

    return {
        "citizen": citizen,
        "officer_a": officer_a,
        "officer_b": officer_b,
        "supervisor_a": supervisor_a,
        "supervisor_b": supervisor_b,
        "g1": g1,
        "g2": g2
    }

@pytest.mark.asyncio
async def test_citizen_forbidden_hold_abort(hold_test_data):
    citizen = hold_test_data["citizen"]
    g1 = hold_test_data["g1"]
    headers = get_auth_headers(citizen)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Hold
        res = await ac.post(f"/api/v1/grievances/{g1.id}/hold", headers=headers, json={
            "reason": "WAITING_ON_MATERIALS",
            "expected_resume_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
            "note": "Citizen cannot hold"
        })
        assert res.status_code == 403

        # Resume
        res = await ac.post(f"/api/v1/grievances/{g1.id}/resume", headers=headers, json={"note": "Citizen cannot resume"})
        assert res.status_code == 403

        # Abort request
        res = await ac.post(f"/api/v1/grievances/{g1.id}/abort-request", headers=headers, json={
            "reason": "DUPLICATE_ISSUE",
            "note": "Citizen cannot request abort"
        })
        assert res.status_code == 403

        # Abort review
        res = await ac.post(f"/api/v1/grievances/{g1.id}/abort-review", headers=headers, json={
            "action": "APPROVE",
            "reason": "Citizen cannot review abort"
        })
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_ownership_enforcement(hold_test_data):
    officer_b = hold_test_data["officer_b"] # Assigned to g2, not g1
    g1 = hold_test_data["g1"]
    headers = get_auth_headers(officer_b)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Officer B tries to hold Grievance 1 (assigned to Officer A)
        res = await ac.post(f"/api/v1/grievances/{g1.id}/hold", headers=headers, json={
            "reason": "WAITING_ON_MATERIALS",
            "expected_resume_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        })
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_supervisor_jurisdiction(hold_test_data):
    supervisor_b = hold_test_data["supervisor_b"] # Water Dept
    g1 = hold_test_data["g1"] # Roads Dept
    headers = get_auth_headers(supervisor_b)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Move g1 into ABORT_PENDING_REVIEW first (need Officer A token)
        officer_a = hold_test_data["officer_a"]
        off_headers = get_auth_headers(officer_a)
        
        # Officer A starts work and requests abort
        await ac.post(f"/api/v1/grievances/{g1.id}/start", headers=off_headers)
        await ac.post(f"/api/v1/grievances/{g1.id}/abort-request", headers=off_headers, json={
            "reason": "DUPLICATE_ISSUE",
            "note": "Requesting abort"
        })

        # Supervisor B (Water Dept) tries to review abort of g1 (Roads Dept)
        res = await ac.post(f"/api/v1/grievances/{g1.id}/abort-review", headers=headers, json={
            "action": "APPROVE"
        })
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_hold_resume_abort_lifecycle(db_session, hold_test_data):
    officer_a = hold_test_data["officer_a"]
    supervisor_a = hold_test_data["supervisor_a"]
    g1 = hold_test_data["g1"]
    
    headers_off = get_auth_headers(officer_a)
    headers_sup = get_auth_headers(supervisor_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. State: ASSIGNED -> ON_HOLD
        resume_time = datetime.now(timezone.utc) + timedelta(days=5)
        res = await ac.post(f"/api/v1/grievances/{g1.id}/hold", headers=headers_off, json={
            "reason": "WAITING_ON_MATERIALS",
            "expected_resume_at": resume_time.isoformat(),
            "note": "Lack of asphalt"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_state"] == "ON_HOLD"

        # Verify hold data in event log
        result_events = await db_session.execute(
            select(GrievanceEvent)
            .where(GrievanceEvent.grievance_id == g1.id, GrievanceEvent.to_state == "ON_HOLD")
        )
        hold_event = result_events.scalars().first()
        assert hold_event is not None
        assert hold_event.event_type == "GRIEVANCE_HELD"
        assert hold_event.from_state == "ASSIGNED"
        assert hold_event.reason == "WAITING_ON_MATERIALS"
        assert hold_event.metadata_json["note"] == "Lack of asphalt"
        assert hold_event.metadata_json["expected_resume_at"] is not None

        # 2. State: ON_HOLD -> IN_PROGRESS (Resume)
        res = await ac.post(f"/api/v1/grievances/{g1.id}/resume", headers=headers_off, json={
            "note": "Asphalt arrived"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_state"] == "IN_PROGRESS"

        # Verify resume event
        result_events = await db_session.execute(
            select(GrievanceEvent)
            .where(GrievanceEvent.grievance_id == g1.id, GrievanceEvent.event_type == "WORK_RESUMED")
        )
        resume_event = result_events.scalars().first()
        assert resume_event is not None
        assert resume_event.from_state == "ON_HOLD"
        assert resume_event.to_state == "IN_PROGRESS"
        assert resume_event.metadata_json["note"] == "Asphalt arrived"

        # 3. State: IN_PROGRESS -> ABORT_PENDING_REVIEW
        res = await ac.post(f"/api/v1/grievances/{g1.id}/abort-request", headers=headers_off, json={
            "reason": "DUPLICATE_ISSUE",
            "note": "Work duplicated with roads-09"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_state"] == "ABORT_PENDING_REVIEW"

        # Verify abort request event
        result_events = await db_session.execute(
            select(GrievanceEvent)
            .where(GrievanceEvent.grievance_id == g1.id, GrievanceEvent.to_state == "ABORT_PENDING_REVIEW")
        )
        abort_req_event = result_events.scalars().first()
        assert abort_req_event is not None
        assert abort_req_event.event_type == "ABORT_REQUESTED"
        assert abort_req_event.reason == "DUPLICATE_ISSUE"
        assert abort_req_event.metadata_json["note"] == "Work duplicated with roads-09"

        # 4. State: ABORT_PENDING_REVIEW -> ABORTED (Supervisor Approve)
        res = await ac.post(f"/api/v1/grievances/{g1.id}/abort-review", headers=headers_sup, json={
            "action": "APPROVE",
            "reason": "Approved since duplicate is confirmed"
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_state"] == "ABORTED"

        # Verify abort approval event
        result_events = await db_session.execute(
            select(GrievanceEvent)
            .where(GrievanceEvent.grievance_id == g1.id, GrievanceEvent.to_state == "ABORTED")
        )
        abort_app_event = result_events.scalars().first()
        assert abort_app_event is not None
        assert abort_app_event.event_type == "ABORT_APPROVED"
        assert abort_app_event.reason == "Approved since duplicate is confirmed"

        # Verify assignment is deactivated
        result_assign = await db_session.execute(
            select(Assignment).where(Assignment.grievance_id == g1.id, Assignment.is_active == True)
        )
        assert result_assign.scalars().first() is None

@pytest.mark.asyncio
async def test_abort_rejection(db_session, hold_test_data):
    officer_a = hold_test_data["officer_a"]
    supervisor_a = hold_test_data["supervisor_a"]
    g1 = hold_test_data["g1"]
    
    headers_off = get_auth_headers(officer_a)
    headers_sup = get_auth_headers(supervisor_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Move to ACKNOWLEDGED first
        await ac.post(f"/api/v1/grievances/{g1.id}/acknowledge", headers=headers_off)
        # Move to IN_PROGRESS
        await ac.post(f"/api/v1/grievances/{g1.id}/start", headers=headers_off)
        
        # Move to ABORT_PENDING_REVIEW
        await ac.post(f"/api/v1/grievances/{g1.id}/abort-request", headers=headers_off, json={
            "reason": "DUPLICATE_ISSUE",
            "note": "Work duplicated"
        })

        # Supervisor Rejects Abort
        res = await ac.post(f"/api/v1/grievances/{g1.id}/abort-review", headers=headers_sup, json={
            "action": "REJECT",
            "reason": "Not a duplicate. Please continue work."
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_state"] == "IN_PROGRESS"

        # Verify rejection event log
        result_events = await db_session.execute(
            select(GrievanceEvent)
            .where(GrievanceEvent.grievance_id == g1.id, GrievanceEvent.event_type == "ABORT_REJECTED")
        )
        rej_event = result_events.scalars().first()
        assert rej_event is not None
        assert rej_event.from_state == "ABORT_PENDING_REVIEW"
        assert rej_event.to_state == "IN_PROGRESS"
        assert rej_event.reason == "Not a duplicate. Please continue work."

@pytest.mark.asyncio
async def test_invalid_transitions(hold_test_data):
    officer_a = hold_test_data["officer_a"]
    g1 = hold_test_data["g1"]
    headers = get_auth_headers(officer_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. State starts at ASSIGNED. Let's resolve it to make it RESOLVED/CLOSED
        # We can simulate this by setting it to IN_PROGRESS first, then resolving
        await ac.post(f"/api/v1/grievances/{g1.id}/acknowledge", headers=headers)
        await ac.post(f"/api/v1/grievances/{g1.id}/start", headers=headers)
        res = await ac.post(f"/api/v1/grievances/{g1.id}/resolve", headers=headers, json={
            "resolution_notes": "Issue is fixed"
        })
        assert res.status_code == 200

        # Now try to transition RESOLUTION_SUBMITTED directly to ON_HOLD
        res = await ac.post(f"/api/v1/grievances/{g1.id}/hold", headers=headers, json={
            "reason": "WAITING_ON_MATERIALS",
            "expected_resume_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        })
        assert res.status_code == 400 # Invalid state transition

@pytest.mark.asyncio
async def test_concurrency_hold(hold_test_data):
    officer_a = hold_test_data["officer_a"]
    g1 = hold_test_data["g1"]
    headers = get_auth_headers(officer_a)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First request succeeds
        res1 = await ac.post(f"/api/v1/grievances/{g1.id}/hold", headers=headers, json={
            "reason": "WAITING_ON_MATERIALS",
            "expected_resume_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        })
        assert res1.status_code == 200

        # Second request fails because it's already ON_HOLD and double hold is not allowed
        res2 = await ac.post(f"/api/v1/grievances/{g1.id}/hold", headers=headers, json={
            "reason": "WAITING_ON_MATERIALS",
            "expected_resume_at": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        })
        assert res2.status_code == 400
