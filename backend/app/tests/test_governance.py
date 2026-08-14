import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.main import app
from app.core.config import settings
from app.core.security import hash_password, create_access_token
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.grievance import Grievance
from app.models.grievance_event import GrievanceEvent
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from app.models.governance import SLAPolicy, AccountabilityDossier, Notification, SystemSetting
from app.governance.services import (
    get_current_time,
    get_sla_policy,
    calculate_risk_score,
    evaluate_grievance_slas,
    trigger_escalation_level3
)
from app.services.grievance_service import create_grievance, transition_grievance

@pytest_asyncio.fixture
async def test_dept_b(db_session):
    dept = Department(name="Dept Governance B", code="DEPT_GOV_B", is_active=True)
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept

@pytest_asyncio.fixture
async def test_citizen_1(db_session):
    user = User(
        email="citizen_gov1@sara.com",
        full_name="Citizen Gov One",
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
        email="officer_gov_a@sara.com",
        full_name="Officer Gov A",
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
async def test_supervisor_a(db_session, test_dept_a):
    user = User(
        email="supervisor_gov_a@sara.com",
        full_name="Supervisor Gov A",
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
        email="supervisor_gov_b@sara.com",
        full_name="Supervisor Gov B",
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
        email="admin_gov@sara.com",
        full_name="Admin Gov",
        password_hash=hash_password("password"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_sla_policy_selection(db_session, test_dept_a):
    # 1. Fallback Policy Selection when DB is empty
    policy_fallback = await get_sla_policy(db_session, test_dept_a.id, "CRITICAL")
    assert policy_fallback.sla_hours == 4
    
    policy_fallback_high = await get_sla_policy(db_session, test_dept_a.id, "HIGH")
    assert policy_fallback_high.sla_hours == 24

    # 2. Configured Policy Selection
    db_policy = SLAPolicy(department_id=test_dept_a.id, priority="CRITICAL", sla_hours=8)
    db_session.add(db_policy)
    await db_session.commit()

    policy_custom = await get_sla_policy(db_session, test_dept_a.id, "CRITICAL")
    assert policy_custom.sla_hours == 8


@pytest.mark.asyncio
async def test_admin_policy_management(db_session, test_dept_a, test_citizen_1, test_admin):
    # Generate tokens
    admin_token = create_access_token(test_admin.id, test_admin.role.value)
    citizen_token = create_access_token(test_citizen_1.id, test_citizen_1.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Citizen creates policy -> 403
        res = await ac.post(
            f"{settings.API_V1_STR}/admin/policies",
            json={"department_id": str(test_dept_a.id), "priority": "CRITICAL", "sla_hours": 12},
            headers={"Authorization": f"Bearer {citizen_token}"}
        )
        assert res.status_code == 403

        # 2. Admin creates policy -> 200
        res = await ac.post(
            f"{settings.API_V1_STR}/admin/policies",
            json={"department_id": str(test_dept_a.id), "priority": "CRITICAL", "sla_hours": 12},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        policy_data = res.json()
        assert policy_data["sla_hours"] == 12

        # 3. Admin lists policies -> 200
        res = await ac.get(
            f"{settings.API_V1_STR}/admin/policies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        assert len(res.json()) >= 1

        # 4. Admin updates policy -> 200
        res = await ac.post(
            f"{settings.API_V1_STR}/admin/policies",
            json={"department_id": str(test_dept_a.id), "priority": "CRITICAL", "sla_hours": 6},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        assert res.json()["sla_hours"] == 6

        # 5. Admin deletes policy -> 204
        policy_id = policy_data["id"]
        res = await ac.delete(
            f"{settings.API_V1_STR}/admin/policies/{policy_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 204


@pytest.mark.asyncio
async def test_admin_only_time_simulation(db_session, test_citizen_1, test_admin):
    admin_token = create_access_token(test_admin.id, test_admin.role.value)
    citizen_token = create_access_token(test_citizen_1.id, test_citizen_1.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Non-admin simulation fails -> 403
        res = await ac.post(
            f"{settings.API_V1_STR}/admin/demo/advance-time",
            json={"offset_seconds": 3600},
            headers={"Authorization": f"Bearer {citizen_token}"}
        )
        assert res.status_code == 403

        # 2. Admin simulation succeeds -> 200
        res = await ac.post(
            f"{settings.API_V1_STR}/admin/demo/advance-time",
            json={"offset_seconds": 7200},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        assert res.json()["total_offset_seconds"] == 7200

        # Check time-travel offset is applied
        sim_time = await get_current_time(db_session)
        real_now = datetime.now(timezone.utc)
        assert (sim_time - real_now).total_seconds() > 7000

        # 3. Disable simulation in production
        original_env = settings.ENVIRONMENT
        settings.ENVIRONMENT = "production"
        try:
            res = await ac.post(
                f"{settings.API_V1_STR}/admin/demo/advance-time",
                json={"offset_seconds": 3600},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert res.status_code == 403
            
            # Verify simulated time ignores offset in production
            prod_time = await get_current_time(db_session)
            assert abs((prod_time - datetime.now(timezone.utc)).total_seconds()) < 5
        finally:
            settings.ENVIRONMENT = original_env


@pytest.mark.asyncio
async def test_deterministic_risk_score_and_breakdown(db_session, test_dept_a, test_citizen_1, test_officer_a, test_supervisor_a, test_admin):
    # Setup SLA Policy (Dept A, HIGH = 24h)
    policy = SLAPolicy(department_id=test_dept_a.id, priority="HIGH", sla_hours=24)
    db_session.add(policy)
    await db_session.commit()

    # Create Grievance
    g = await create_grievance(db_session, test_citizen_1, "Water Leak", "Desc", "Loc")
    
    # Progress state machine: SUBMITTED -> CLASSIFIED -> ROUTED -> ASSIGNED
    await transition_grievance(db_session, g.id, "CLASSIFIED", test_admin, payload={"category": "Water", "priority": "HIGH"})
    await transition_grievance(db_session, g.id, "ROUTED", test_admin, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})

    # Fetch fresh grievance with events
    result = await db_session.execute(
        select(Grievance).where(Grievance.id == g.id).options(selectinload(Grievance.events))
    )
    g = result.scalars().first()

    # 1. Base Score calculation (No breach, no delay, active work)
    now = datetime.now(timezone.utc)
    score, factors = await calculate_risk_score(db_session, g, now)
    assert score == 0
    assert len(factors) == 0

    # 2. Test SLA Proximity (Elapsed time >= 80% of 24h -> 20 hours elapsed)
    future_prox = now + timedelta(hours=20)
    score, factors = await calculate_risk_score(db_session, g, future_prox)
    assert factors["sla_proximity"] == 15
    assert score == 15

    # 3. Test SLA Breach (Elapsed time > 24h -> 25 hours elapsed)
    future_breach = now + timedelta(hours=25)
    score, factors = await calculate_risk_score(db_session, g, future_breach)
    assert factors["sla_breach"] == 35
    assert "sla_proximity" not in factors
    assert factors["missed_milestone"] == 15
    assert score == 50

    # 4. Test Officer Inactivity (> 48 hours without update)
    future_inactivity = now + timedelta(hours=50)
    score, factors = await calculate_risk_score(db_session, g, future_inactivity)
    assert factors["officer_inactivity"] == 20
    # Also triggers SLA breach (50h > 24h) and missed milestone (50h > 24h)
    assert factors["sla_breach"] == 35
    assert factors["missed_milestone"] == 15
    assert score == 70

    # 5. Test Citizen Rejections (Capped at max 40 points)
    # Simulate first rejection
    await transition_grievance(db_session, g.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Completed fix"})
    await transition_grievance(db_session, g.id, "VERIFICATION", test_admin)
    
    # Citizen rejects -> Reopen 1
    await transition_grievance(db_session, g.id, "REOPENED", test_citizen_1, payload={"reason": "Still leaking"})
    
    # Officer resolves and citizen rejects -> Reopen 2
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Completely done"})
    await transition_grievance(db_session, g.id, "VERIFICATION", test_admin)
    await transition_grievance(db_session, g.id, "REOPENED", test_citizen_1, payload={"reason": "Leaking again"})

    # Officer resolves and citizen rejects -> Reopen 3 (Count: 3, points: 60, capped at 40)
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Re-fixed"})
    await transition_grievance(db_session, g.id, "VERIFICATION", test_admin)
    await transition_grievance(db_session, g.id, "REOPENED", test_citizen_1, payload={"reason": "Still not fixed"})

    # Refresh g to load all events
    await db_session.refresh(g)
    score, factors = await calculate_risk_score(db_session, g, now)
    assert factors["citizen_rejection"] == 40 # Capped at 40
    assert score <= 100


@pytest.mark.asyncio
async def test_sla_monitoring_warnings_and_breaches(db_session, test_dept_a, test_citizen_1, test_officer_a, test_supervisor_a, test_admin):
    # Setup Policy
    policy = SLAPolicy(department_id=test_dept_a.id, priority="CRITICAL", sla_hours=4)
    db_session.add(policy)
    await db_session.commit()

    # Create Grievance
    g = await create_grievance(db_session, test_citizen_1, "Critical Wire Sparking", "Desc", "Loc")
    await transition_grievance(db_session, g.id, "CLASSIFIED", test_admin, payload={"category": "Electrical", "priority": "CRITICAL"})
    await transition_grievance(db_session, g.id, "ROUTED", test_admin, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})

    # 1. Evaluate SLAs immediately -> Nothing should happen
    await evaluate_grievance_slas(db_session)
    
    # Query events
    res_events = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    events = res_events.scalars().all()
    assert not any(e.event_type == "SLA_WARNING" for e in events)
    assert not any(e.event_type == "SLA_BREACHED" for e in events)

    # 2. Advance time to warning threshold (80% of 4 hours = 3.2 hours = 11520 seconds)
    time_setting = SystemSetting(key="time_offset_seconds", value="12000")
    db_session.add(time_setting)
    await db_session.commit()

    # Evaluate SLAs -> Should trigger SLA_WARNING
    await evaluate_grievance_slas(db_session)
    
    res_events = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    events = res_events.scalars().all()
    assert any(e.event_type == "SLA_WARNING" for e in events)
    assert not any(e.event_type == "SLA_BREACHED" for e in events)

    # Duplicate Prevention: Run SLA check again. No new events should be created.
    warn_events_count_1 = sum(1 for e in events if e.event_type == "SLA_WARNING")
    await evaluate_grievance_slas(db_session)
    
    res_events = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    events = res_events.scalars().all()
    warn_events_count_2 = sum(1 for e in events if e.event_type == "SLA_WARNING")
    assert warn_events_count_1 == warn_events_count_2

    # 3. Advance time past deadline (4.5 hours = 16200 seconds)
    time_setting.value = "17000"
    await db_session.commit()

    # Evaluate SLAs -> Should trigger SLA_BREACHED, escalate, and create dossier
    await evaluate_grievance_slas(db_session)
    
    res_events = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    events = res_events.scalars().all()
    assert any(e.event_type == "SLA_BREACHED" for e in events)
    
    # Check dossier exists
    res_dossier = await db_session.execute(select(AccountabilityDossier).where(AccountabilityDossier.grievance_id == g.id))
    dossier = res_dossier.scalars().first()
    assert dossier is not None
    assert dossier.risk_score > 0

    # Verify grievance status remains unchanged (No auto reassignment, no auto-closure)
    await db_session.refresh(g)
    assert g.current_state == "ASSIGNED"
    assert g.escalated is True
    assert g.escalation_level == 2


@pytest.mark.asyncio
async def test_escalation_level3_on_citizen_rejection(db_session, test_dept_a, test_citizen_1, test_officer_a, test_supervisor_a, test_admin):
    # Setup
    policy = SLAPolicy(department_id=test_dept_a.id, priority="HIGH", sla_hours=24)
    db_session.add(policy)
    await db_session.commit()

    g = await create_grievance(db_session, test_citizen_1, "Gravel Repair", "Desc", "Loc")
    await transition_grievance(db_session, g.id, "CLASSIFIED", test_admin, payload={"category": "Roads", "priority": "HIGH"})
    await transition_grievance(db_session, g.id, "ROUTED", test_admin, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Filled gravel"})
    await transition_grievance(db_session, g.id, "VERIFICATION", test_admin)

    # Citizen rejects resolution -> transitions to REOPENED and triggers Level 3 escalation
    await transition_grievance(db_session, g.id, "REOPENED", test_citizen_1, payload={"reason": "Pothole still visible"})

    await db_session.refresh(g)
    assert g.current_state == "REOPENED"
    assert g.escalated is True
    assert g.escalation_level == 3
    assert g.risk_score > 0
    assert g.risk_factors["citizen_rejection"] == 20

    # Verify dossier generated and contains rejections count
    res_dossier = await db_session.execute(select(AccountabilityDossier).where(AccountabilityDossier.grievance_id == g.id))
    dossier = res_dossier.scalars().first()
    assert dossier is not None
    assert dossier.risk_score == g.risk_score


@pytest.mark.asyncio
async def test_supervisor_access_restrictions(db_session, test_dept_a, test_dept_b, test_citizen_1, test_officer_a, test_supervisor_a, test_supervisor_b, test_admin):
    # Setup
    policy = SLAPolicy(department_id=test_dept_a.id, priority="HIGH", sla_hours=24)
    db_session.add(policy)
    await db_session.commit()

    g = await create_grievance(db_session, test_citizen_1, "Wire Leak", "Desc", "Loc")
    await transition_grievance(db_session, g.id, "CLASSIFIED", test_admin, payload={"category": "Electrical", "priority": "HIGH"})
    await transition_grievance(db_session, g.id, "ROUTED", test_admin, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})

    # Generate dossier manually
    dossier = AccountabilityDossier(grievance_id=g.id, risk_score=10, risk_factors={})
    db_session.add(dossier)
    await db_session.commit()

    # Generate tokens
    sup_a_token = create_access_token(test_supervisor_a.id, test_supervisor_a.role.value)
    sup_b_token = create_access_token(test_supervisor_b.id, test_supervisor_b.role.value)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Supervisor A (Same department) views dossier list -> 200
        res = await ac.get(f"{settings.API_V1_STR}/supervisor/dossiers", headers={"Authorization": f"Bearer {sup_a_token}"})
        assert res.status_code == 200
        assert len(res.json()) == 1

        # 2. Supervisor B (Different department) views dossier list -> 200 (but list is empty)
        res = await ac.get(f"{settings.API_V1_STR}/supervisor/dossiers", headers={"Authorization": f"Bearer {sup_b_token}"})
        assert res.status_code == 200
        assert len(res.json()) == 0

        # 3. Supervisor A retrieves specific dossier -> 200
        res = await ac.get(f"{settings.API_V1_STR}/supervisor/dossiers/{dossier.id}", headers={"Authorization": f"Bearer {sup_a_token}"})
        assert res.status_code == 200

        # 4. Supervisor B retrieves specific dossier -> 403 (mismatch)
        res = await ac.get(f"{settings.API_V1_STR}/supervisor/dossiers/{dossier.id}", headers={"Authorization": f"Bearer {sup_b_token}"})
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_audit_logs_and_database_immutability(db_session, test_dept_a, test_citizen_1, test_admin):
    g = await create_grievance(db_session, test_citizen_1, "Wire Leak", "Desc", "Loc")
    
    # Verify events are written
    res_events = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.grievance_id == g.id))
    events = res_events.scalars().all()
    assert len(events) >= 1
    event = events[0]

    # Database Immutability Check: Attempting to delete a GrievanceEvent should be ignored by DB rules
    await db_session.execute(text(f"DELETE FROM grievance_events WHERE id = '{event.id}'"))
    await db_session.commit()

    # Verify event still exists
    res_check = await db_session.execute(select(GrievanceEvent).where(GrievanceEvent.id == event.id))
    assert res_check.scalars().first() is not None

    # Attempting to update a GrievanceEvent should be ignored
    original_type = event.event_type
    await db_session.execute(text(f"UPDATE grievance_events SET event_type = 'HACKED' WHERE id = '{event.id}'"))
    await db_session.commit()

    # Verify event unchanged
    await db_session.refresh(event)
    assert event.event_type == original_type


@pytest.mark.asyncio
async def test_transaction_rollback_governance(db_session, test_dept_a, test_citizen_1, test_officer_a, test_supervisor_a, test_admin):
    policy = SLAPolicy(department_id=test_dept_a.id, priority="HIGH", sla_hours=24)
    db_session.add(policy)
    await db_session.commit()

    g = await create_grievance(db_session, test_citizen_1, "Gravel Repair", "Desc", "Loc")
    await transition_grievance(db_session, g.id, "CLASSIFIED", test_admin, payload={"category": "Roads", "priority": "HIGH"})
    await transition_grievance(db_session, g.id, "ROUTED", test_admin, payload={"department_id": str(test_dept_a.id)})
    await transition_grievance(db_session, g.id, "ASSIGNED", test_supervisor_a, payload={"officer_id": str(test_officer_a.id)})
    await transition_grievance(db_session, g.id, "ACKNOWLEDGED", test_officer_a)
    await transition_grievance(db_session, g.id, "IN_PROGRESS", test_officer_a)
    await transition_grievance(db_session, g.id, "RESOLUTION_SUBMITTED", test_officer_a, payload={"resolution_notes": "Done"})
    await transition_grievance(db_session, g.id, "VERIFICATION", test_admin)

    # Induce error during Level 3 escalation: We can mock calculate_risk_score to raise an Exception
    # Let's verify that the entire state transition fails and rolls back, leaving the grievance state as VERIFICATION
    # (instead of transitioning to REOPENED but having a broken escalation state)
    import app.governance.services
    original_risk_calc = app.governance.services.calculate_risk_score

    async def mock_fail_risk_calc(*args, **kwargs):
        raise RuntimeError("Database connection failure simulation")

    app.governance.services.calculate_risk_score = mock_fail_risk_calc
    
    try:
        with pytest.raises(Exception):
            await transition_grievance(db_session, g.id, "REOPENED", test_citizen_1, payload={"reason": "Broken"})
            
        # Verify that state remains VERIFICATION (rolled back)
        await db_session.refresh(g)
        assert g.current_state == "VERIFICATION"
    finally:
        # Restore mock
        app.governance.services.calculate_risk_score = original_risk_calc
