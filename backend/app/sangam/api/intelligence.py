import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User, UserRole
from app.sangam.models import NeedCluster, IntelligenceAlert, InvestmentMatch
from app.sangam.schemas import (
    SangamOverviewResponse,
    NeedClusterResponse,
    IntelligenceAlertResponse,
    InvestmentMatchResponse,
    NeedEvidenceDrawerResponse
)
from app.sangam.services.clustering_service import NeedClusteringService
from app.sangam.services.investment_service import InvestmentService
from app.sangam.services.gap_detection_service import GapDetectionService
from app.sangam.repositories.intelligence_repository import IntelligenceRepository

router = APIRouter(prefix="/sangam", tags=["sangam_intelligence"])

clustering_service = NeedClusteringService()
investment_service = InvestmentService()
gap_detection_service = GapDetectionService()
intelligence_repo = IntelligenceRepository()


def verify_sangam_access(current_user: User) -> Optional[uuid.UUID]:
    """Ensures Citizens cannot access Sangam. Returns department_id for Officers/Supervisors."""
    if current_user.role == UserRole.CITIZEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Sangam Civic Intelligence is restricted to administrative and operational staff."
        )
    if current_user.role in [UserRole.SUPERVISOR, UserRole.OFFICER]:
        return current_user.department_id
    return None


async def _run_sangam_intelligence_pipeline(db: AsyncSession):
    """Triggers clustering, project matching, and gap detection synchronization."""
    await clustering_service.synchronize_need_clusters(db)
    await investment_service.seed_demo_projects_if_empty(db)
    await investment_service.match_projects_to_clusters(db)
    await gap_detection_service.analyze_and_generate_alerts(db)


@router.get("/overview", response_model=SangamOverviewResponse)
async def get_sangam_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)
    metrics = await intelligence_repo.get_overview_metrics(db, department_id=dept_id)
    return metrics


@router.get("/needs", response_model=List[NeedClusterResponse])
async def list_need_clusters(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)

    query = select(NeedCluster).options(selectinload(NeedCluster.department))
    if dept_id:
        query = query.where(NeedCluster.department_id == dept_id)

    res = await db.execute(query.order_by(NeedCluster.priority_score.desc()))
    return list(res.scalars().all())


@router.get("/needs/{need_id}", response_model=NeedClusterResponse)
async def get_need_cluster(
    need_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    res = await db.execute(
        select(NeedCluster)
        .where(NeedCluster.id == need_id)
        .options(selectinload(NeedCluster.department))
    )
    cluster = res.scalars().first()
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need cluster not found")
    if dept_id and cluster.department_id and cluster.department_id != dept_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied for department")

    return cluster


@router.get("/needs/{need_id}/evidence", response_model=NeedEvidenceDrawerResponse)
async def get_need_cluster_evidence(
    need_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)
    evidence_data = await intelligence_repo.get_evidence_drawer_data(db, need_id)
    if not evidence_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Need cluster not found")

    return evidence_data


@router.get("/hotspots", response_model=List[NeedClusterResponse])
async def list_hotspots(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)

    query = select(NeedCluster).where(NeedCluster.priority_score >= 40.0).options(selectinload(NeedCluster.department))
    if dept_id:
        query = query.where(NeedCluster.department_id == dept_id)

    res = await db.execute(query.order_by(NeedCluster.priority_score.desc()))
    return list(res.scalars().all())


@router.get("/gaps", response_model=List[IntelligenceAlertResponse])
async def list_gaps_and_mismatches(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)

    query = select(IntelligenceAlert).where(
        IntelligenceAlert.type.in_(["UNSERVED_GAP", "POTENTIAL_OUTCOME_MISMATCH"])
    ).options(selectinload(IntelligenceAlert.need_cluster), selectinload(IntelligenceAlert.government_project))

    res = await db.execute(query.order_by(IntelligenceAlert.created_at.desc()))
    alerts = res.scalars().all()
    if dept_id:
        alerts = [a for a in alerts if a.need_cluster and a.need_cluster.department_id == dept_id]

    return alerts


@router.get("/alerts", response_model=List[IntelligenceAlertResponse])
async def list_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)

    query = select(IntelligenceAlert).options(
        selectinload(IntelligenceAlert.need_cluster),
        selectinload(IntelligenceAlert.government_project)
    )
    res = await db.execute(query.order_by(IntelligenceAlert.created_at.desc()))
    alerts = res.scalars().all()
    if dept_id:
        alerts = [a for a in alerts if a.need_cluster and a.need_cluster.department_id == dept_id]

    return alerts


@router.get("/priorities", response_model=List[NeedClusterResponse])
async def list_priority_areas(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dept_id = verify_sangam_access(current_user)
    await _run_sangam_intelligence_pipeline(db)

    query = select(NeedCluster).options(selectinload(NeedCluster.department))
    if dept_id:
        query = query.where(NeedCluster.department_id == dept_id)

    res = await db.execute(query.order_by(NeedCluster.priority_score.desc()))
    return list(res.scalars().all())
