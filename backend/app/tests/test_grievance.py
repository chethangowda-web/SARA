import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.future import select

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.grievance_event import GrievanceEvent
from app.models.assignment import Assignment
from app.models.audit import AuditLog


@pytest_asyncio.fixture
async def test_dept_b(db_session):
    dept = Department(name="Dept B", code="DEPT_B", is_active=True)
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept

@pytest_asyncio.fixture
async def test_citizen_1(db_session):
    user = User(
        email="citizen1@sara.com",
        full_name="Citizen One",
        password_hash=hash_password("password"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_citizen_2(db_session):
    user = User(
        email="citizen2@sara.com",
        full_name="Citizen Two",
        password_hash=hash_password("password"),
        role=UserRole.CITIZEN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_officer_a(db_session, test_dept_a):
    user = User(
        email="officer_a@sara.com",
        full_name="Officer A",
        password_hash=hash_password("password"),
        role=UserRole.OFFICER,
        department_id=test_dept_a.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_officer_b(db_session, test_dept_b):
    user = User(
        email="officer_b@sara.com",
        full_name="Officer B",
        password_hash=hash_password("password"),
        role=UserRole.OFFICER,
        department_id=test_dept_b.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_inactive_officer(db_session, test_dept_a):
    user = User(
        email="officer_inactive@sara.com",
        full_name="Inactive Officer",
        password_hash=hash_password("password"),
        role=UserRole.OFFICER,
        department_id=test_dept_a.id,
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_supervisor_a(db_session, test_dept_a):
    user = User(
        email="supervisor_a@sara.com",
        full_name="Supervisor A",
        password_hash=hash_password("password"),
        role=UserRole.SUPERVISOR,
        department_id=test_dept_a.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_supervisor_b(db_session, test_dept_b):
    user = User(
        email="supervisor_b@sara.com",
        full_name="Supervisor B",
        password_hash=hash_password("password"),
        role=UserRole.SUPERVISOR,
        department_id=test_dept_b.id,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def test_admin(db_session):
    user = User(
        email="admin_override@sara.com",
        full_name="Admin",
        password_hash=hash_password("password"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.mark.asyncio
async def test_citizen_can_create_grievance_and_starts_classified(test_citizen_1):
    token = create_access_token(test_citizen_1.id, test_citizen_1.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Water leakage in sector 4",
                "description": "Main pipes are leaking and wasting clean drinking water.",
                "location": "Sector 4, Main Road"
            }
        )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Water leakage in sector 4"
    assert data["current_state"] == "CLASSIFIED"
    assert data["submitted_at"] is not None
    assert data["citizen_id"] == str(test_citizen_1.id)

@pytest.mark.asyncio
async def test_citizen_ownership_boundaries(db_session, test_citizen_1, test_citizen_2):
    # Citizen 1 submits
    token1 = create_access_token(test_citizen_1.id, test_citizen_1.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/grievances",
            headers={"Authorization": f"Bearer {token1}"},
            json={
                "title": "Road pothole on block B",
                "description": "A deep pothole is causing accidents.",
                "location": "Block B, Main street"
            }
        )
        grievance_id = res.json()["id"]

        # Citizen 1 reads (should work)
        res_read1 = await ac.get(
            f"{settings.API_V1_STR}/grievances/{grievance_id}",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert res_read1.status_code == 200

        # Citizen 2 reads (should be blocked)
        token2 = create_access_token(test_citizen_2.id, test_citizen_2.role.value)
        res_read2 = await ac.get(
            f"{settings.API_V1_STR}/grievances/{grievance_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert res_read2.status_code == 403

@pytest.mark.asyncio
async def test_invalid_transitions_are_blocked(db_session, test_citizen_1, test_officer_a):
    # Create grievance
    from app.services.grievance_service import create_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Pipeline leakage", "Location")
    
    # Try to transition SUBMITTED -> IN_PROGRESS directly (Officer/User tries)
    token = create_access_token(test_officer_a.id, test_officer_a.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/start",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 400
    assert "Invalid state transition sequence" in res.json()["detail"]

@pytest.mark.asyncio
async def test_supervisor_assign_officer_rules(db_session, test_citizen_1, test_supervisor_a, test_officer_a, test_officer_b, test_inactive_officer, test_dept_a):
    from app.services.grievance_service import create_grievance, transition_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Pipeline leakage", "Location")
    
    # Move to CLASSIFIED then ROUTED to Dept A
    system_user = User(id=uuid.uuid4(), email="sys@sara.com", full_name="Sys", password_hash="", role=UserRole.ADMIN, is_active=True)
    await transition_grievance(db_session, g.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    
    token_sup = create_access_token(test_supervisor_a.id, test_supervisor_a.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Supervisor cannot assign officer from another department (Officer B is Dept B)
        res_wrong_dept = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/assign",
            headers={"Authorization": f"Bearer {token_sup}"},
            json={"officer_id": str(test_officer_b.id)}
        )
        assert res_wrong_dept.status_code == 400
        
        # 2. Supervisor cannot assign inactive officer
        res_inactive = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/assign",
            headers={"Authorization": f"Bearer {token_sup}"},
            json={"officer_id": str(test_inactive_officer.id)}
        )
        assert res_inactive.status_code == 400
        
        # 3. Valid assignment (Officer A is Dept A)
        res_valid = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/assign",
            headers={"Authorization": f"Bearer {token_sup}"},
            json={"officer_id": str(test_officer_a.id)}
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["current_state"] == "ASSIGNED"

@pytest.mark.asyncio
async def test_assigned_officer_work_flow_to_resolution(db_session, test_citizen_1, test_supervisor_a, test_officer_a, test_officer_b, test_dept_a):
    from app.services.grievance_service import create_grievance, transition_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Pipeline leakage", "Location")
    
    system_user = User(id=uuid.uuid4(), email="sys@sara.com", full_name="Sys", password_hash="", role=UserRole.ADMIN, is_active=True)
    await transition_grievance(db_session, g.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    
    token_off_a = create_access_token(test_officer_a.id, test_officer_a.role.value)
    token_off_b = create_access_token(test_officer_b.id, test_officer_b.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Officer B (non-assigned) tries to acknowledge (fails)
        res_b = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/acknowledge",
            headers={"Authorization": f"Bearer {token_off_b}"}
        )
        assert res_b.status_code == 403
        
        # Officer A acknowledges (succeeds)
        res_a = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/acknowledge",
            headers={"Authorization": f"Bearer {token_off_a}"}
        )
        assert res_a.status_code == 200
        
        # Start work
        res_start = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/start",
            headers={"Authorization": f"Bearer {token_off_a}"}
        )
        assert res_start.status_code == 200
        
        # Submit resolution without notes (fails)
        res_empty = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/resolve",
            headers={"Authorization": f"Bearer {token_off_a}"},
            json={"resolution_notes": ""}
        )
        assert res_empty.status_code == 422 # Pydantic min_length validation or backend 400
        
        # Submit resolution with valid notes -> stays RESOLUTION_SUBMITTED awaiting supervisor review
        res_valid = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/resolve",
            headers={"Authorization": f"Bearer {token_off_a}"},
            json={"resolution_notes": "Repaired leakage by replacing main valve."}
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["current_state"] == "RESOLUTION_SUBMITTED"

@pytest.mark.asyncio
async def test_supervisor_review_resolution_approve_reject(db_session, test_citizen_1, test_supervisor_a, test_supervisor_b, test_officer_a, test_dept_a):
    from app.services.grievance_service import create_grievance, transition_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Pipeline leakage", "Location")

    system_user = User(id=uuid.uuid4(), email="sys@sara.com", full_name="Sys", password_hash="", role=UserRole.ADMIN, is_active=True)
    await transition_grievance(db_session, g.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Fixed the leak."})

    token_sup_a = create_access_token(test_supervisor_a.id, test_supervisor_a.role.value)
    token_sup_b = create_access_token(test_supervisor_b.id, test_supervisor_b.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Supervisor B (different department) cannot review
        res_wrong_dept = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/review",
            headers={"Authorization": f"Bearer {token_sup_b}"},
            json={"action": "APPROVE"}
        )
        assert res_wrong_dept.status_code == 403

        # Supervisor A approves -> VERIFICATION
        res_approve = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/review",
            headers={"Authorization": f"Bearer {token_sup_a}"},
            json={"action": "APPROVE"}
        )
        assert res_approve.status_code == 200
        assert res_approve.json()["current_state"] == "VERIFICATION"

    # Rejection flow
    g2 = await create_grievance(db_session, test_citizen_1, "Leakage 2", "Pipeline leakage 2", "Location 2")
    await transition_grievance(db_session, g2.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g2.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g2.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g2.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g2.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g2.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Fixed."})

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Reject without reason -> 400
        res_reject_no_reason = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g2.id}/review",
            headers={"Authorization": f"Bearer {token_sup_a}"},
            json={"action": "REJECT"}
        )
        assert res_reject_no_reason.status_code == 400

        # Reject with reason -> IN_PROGRESS (rework)
        res_reject = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g2.id}/review",
            headers={"Authorization": f"Bearer {token_sup_a}"},
            json={"action": "REJECT", "reason": "Evidence incomplete. Please resubmit with photos."}
        )
        assert res_reject.status_code == 200
        assert res_reject.json()["current_state"] == "IN_PROGRESS"

    # After rework, officer can resubmit -> RESOLUTION_SUBMITTED again
    from httpx import AsyncClient as HAC
    async with HAC(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token_off_a = create_access_token(test_officer_a.id, test_officer_a.role.value)
        res_resubmit = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g2.id}/resolve",
            headers={"Authorization": f"Bearer {token_off_a}"},
            json={"resolution_notes": "Updated evidence attached."}
        )
        assert res_resubmit.status_code == 200
        assert res_resubmit.json()["current_state"] == "RESOLUTION_SUBMITTED"

@pytest.mark.asyncio
async def test_citizen_verification_flow(db_session, test_citizen_1, test_citizen_2, test_supervisor_a, test_officer_a, test_dept_a):
    from app.services.grievance_service import create_grievance, transition_grievance
    
    # 1. Acceptance Flow
    g1 = await create_grievance(db_session, test_citizen_1, "Title", "Desc", "Loc")
    system_user = User(id=uuid.uuid4(), email="sys@sara.com", full_name="Sys", password_hash="", role=UserRole.ADMIN, is_active=True)
    await transition_grievance(db_session, g1.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g1.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g1.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g1.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g1.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g1.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Fixed"})
    await transition_grievance(db_session, g1.id, "VERIFICATION", system_user)
    
    token1 = create_access_token(test_citizen_1.id, test_citizen_1.role.value)
    token2 = create_access_token(test_citizen_2.id, test_citizen_2.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Non-owner citizen tries to verify (403)
        res_non_owner = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g1.id}/verify",
            headers={"Authorization": f"Bearer {token2}"},
            json={"action": "ACCEPT"}
        )
        assert res_non_owner.status_code == 403
        
        # Owner accepts -> CLOSED
        res_accept = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g1.id}/verify",
            headers={"Authorization": f"Bearer {token1}"},
            json={"action": "ACCEPT"}
        )
        assert res_accept.status_code == 200
        assert res_accept.json()["current_state"] == "CLOSED"

    # 2. Rejection Flow
    g2 = await create_grievance(db_session, test_citizen_1, "Title 2", "Desc 2", "Loc 2")
    await transition_grievance(db_session, g2.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g2.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g2.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g2.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g2.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g2.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Fixed"})
    await transition_grievance(db_session, g2.id, "VERIFICATION", system_user)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Rejection without explanation (fails)
        res_no_exp = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g2.id}/verify",
            headers={"Authorization": f"Bearer {token1}"},
            json={"action": "REJECT", "reason": ""}
        )
        assert res_no_exp.status_code == 400
        
        # Rejection with explanation -> REOPENED
        res_reject = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g2.id}/verify",
            headers={"Authorization": f"Bearer {token1}"},
            json={"action": "REJECT", "reason": "Water is still leaking."}
        )
        assert res_reject.status_code == 200
        assert res_reject.json()["current_state"] == "REOPENED"

@pytest.mark.asyncio
async def test_supervisor_boundaries(db_session, test_citizen_1, test_supervisor_b, test_dept_a):
    from app.services.grievance_service import create_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Desc", "Loc")
    g.department_id = test_dept_a.id
    await db_session.commit()
    
    token_b = create_access_token(test_supervisor_b.id, test_supervisor_b.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Supervisor B (from Dept B) tries to read Dept A's grievances
        res = await ac.get(
            f"{settings.API_V1_STR}/grievances/{g.id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert res.status_code == 403

@pytest.mark.asyncio
async def test_grievance_events_are_immutable(db_session, test_citizen_1):
    from app.services.grievance_service import create_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Desc", "Loc")
    
    res = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    event = res.scalars().first()
    assert event is not None
    
    # 1. Update blocked
    try:
        await db_session.execute(
            text("UPDATE grievance_events SET event_type = 'MUTATED' WHERE id = :id"),
            {"id": event.id}
        )
        await db_session.commit()
    except Exception:
        pass
    await db_session.refresh(event)
    assert event.event_type == "GRIEVANCE_SUBMITTED"
    
    # 2. Delete blocked
    try:
        await db_session.execute(
            text("DELETE FROM grievance_events WHERE id = :id"),
            {"id": event.id}
        )
        await db_session.commit()
    except Exception:
        pass
    res_deleted = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.id == event.id))
    assert res_deleted.scalars().first() is not None

@pytest.mark.asyncio
async def test_timeline_is_chronological(db_session, test_citizen_1, test_supervisor_a, test_officer_a, test_dept_a):
    from app.services.grievance_service import create_grievance, transition_grievance
    g = await create_grievance(db_session, test_citizen_1, "Title", "Desc", "Loc")
    system_user = User(id=uuid.uuid4(), email="sys@sara.com", full_name="Sys", password_hash="", role=UserRole.ADMIN, is_active=True)
    
    # Execute valid transitions
    await transition_grievance(db_session, g.id, "CLASSIFIED", system_user)
    await transition_grievance(db_session, g.id, "ROUTED", system_user, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    
    token = create_access_token(test_citizen_1.id, test_citizen_1.role.value)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get(
            f"{settings.API_V1_STR}/grievances/{g.id}/timeline",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert res.status_code == 200
    timeline = res.json()
    assert len(timeline) == 4 # SUBMITTED, CLASSIFIED, ROUTED, ASSIGNED
    assert timeline[0]["to_state"] == "SUBMITTED"
    assert timeline[1]["to_state"] == "CLASSIFIED"
    assert timeline[2]["to_state"] == "ROUTED"
    assert timeline[3]["to_state"] == "ASSIGNED"

@pytest.mark.asyncio
async def test_failed_transition_does_not_change_state_and_rolls_back_atomically(db_session, test_citizen_1):
    from app.services.grievance_service import create_grievance, transition_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Desc", "Loc")
    
    # Try invalid transition (SUBMITTED -> IN_PROGRESS)
    system_user = User(id=uuid.uuid4(), email="sys@sara.com", full_name="Sys", password_hash="", role=UserRole.ADMIN, is_active=True)
    with pytest.raises(HTTPException):
        await transition_grievance(db_session, g.id, "IN_PROGRESS", system_user)
        
    # Check that state remains SUBMITTED
    await db_session.refresh(g)
    assert g.current_state == "SUBMITTED"
    
    # Check that no new event was logged
    res_events = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    assert len(res_events.scalars().all()) == 1

@pytest.mark.asyncio
async def test_admin_override_rules(db_session, test_citizen_1, test_admin):
    from app.services.grievance_service import create_grievance
    g = await create_grievance(db_session, test_citizen_1, "Leakage", "Desc", "Loc")
    
    token = create_access_token(test_admin.id, test_admin.role.value)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Override without reason (fails)
        res_no_reason = await ac.post(
            f"{settings.API_V1_STR}/grievances/{g.id}/acknowledge", # Just normal route or we test overrides via service direct
            headers={"Authorization": f"Bearer {token}"}
        )
        # Wait, the normal route /acknowledge calls transition_grievance with normal flow.
        # Let's test admin override directly via service call!
        pass
        
    # Check direct service override call validation:
    # 1. Fails without reason
    from app.services.grievance_service import transition_grievance
    with pytest.raises(HTTPException) as err:
        await transition_grievance(db_session, g.id, "CLOSED", test_admin, is_admin_override=True, override_reason="")
    assert err.value.status_code == 400
    
    # 2. Succeeds with reason and writes EVENT and AUDIT
    g_override = await transition_grievance(
        db_session, g.id, "CLOSED", test_admin, is_admin_override=True, override_reason="Special manual resolution."
    )
    assert g_override.current_state == "CLOSED"
    
    # Verify event logged
    res_event = await db_session.execute(
        select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id, GrievanceEvent.event_type == "ADMIN_OVERRIDE")
    )
    event = res_event.scalars().first()
    assert event is not None
    assert event.reason == "Special manual resolution."
