from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.operations import (
    BackupArtifactRead,
    BackupManifestRead,
    FlattenLiveResult,
    FlattenPaperResult,
    FlattenRunRead,
    PreflightRead,
    ReconcileRunRead,
    RecoveryRunRead,
    ReleaseAcceptanceRunRead,
    ReleaseReadinessRead,
    ReleaseReportRead,
    SystemControlsUpdate,
    SystemStateRead,
)
from app.services.deploy_ops import DeploymentOpsService
from app.services.operations import OperationsError, OperationsService
from app.services.release_manager import ReleaseManagerService

router = APIRouter()


@router.get('/state', response_model=SystemStateRead)
def read_state(db: Session = Depends(db_session)) -> SystemStateRead:
    return SystemStateRead(**OperationsService(db).system_health())


@router.put('/state', response_model=SystemStateRead)
def update_state(payload: SystemControlsUpdate, db: Session = Depends(db_session)) -> SystemStateRead:
    service = OperationsService(db)
    service.update_controls(
        maintenance_mode=payload.maintenance_mode,
        trading_paused=payload.trading_paused,
        kill_switch_armed=payload.kill_switch_armed,
    )
    return SystemStateRead(**service.system_health())


@router.get('/preflight', response_model=PreflightRead)
def read_preflight(db: Session = Depends(db_session)) -> PreflightRead:
    return PreflightRead(**DeploymentOpsService(db).preflight())


@router.get('/release-readiness', response_model=ReleaseReadinessRead)
def read_release_readiness(db: Session = Depends(db_session)) -> ReleaseReadinessRead:
    return ReleaseReadinessRead(**DeploymentOpsService(db).release_readiness())


@router.get('/backups', response_model=list[BackupArtifactRead])
def list_backups(db: Session = Depends(db_session)) -> list[BackupArtifactRead]:
    return [BackupArtifactRead(**item) for item in DeploymentOpsService(db).list_backup_artifacts()]


@router.post('/backup/manifest', response_model=BackupManifestRead)
def create_backup_manifest(db: Session = Depends(db_session)) -> BackupManifestRead:
    return BackupManifestRead(**DeploymentOpsService(db).write_backup_manifest(source='api-manual'))




@router.get('/releases', response_model=list[BackupArtifactRead])
def list_release_artifacts(db: Session = Depends(db_session)) -> list[BackupArtifactRead]:
    return [BackupArtifactRead(**item) for item in ReleaseManagerService(db).list_release_artifacts()]


@router.get('/release-report', response_model=ReleaseReportRead)
def read_release_report(db: Session = Depends(db_session)) -> ReleaseReportRead:
    return ReleaseReportRead(**ReleaseManagerService(db).build_release_report())


@router.post('/release-acceptance/run', response_model=ReleaseAcceptanceRunRead)
def run_release_acceptance(db: Session = Depends(db_session)) -> ReleaseAcceptanceRunRead:
    return ReleaseAcceptanceRunRead(**ReleaseManagerService(db).run_release_acceptance(trigger='api-manual'))


@router.post('/reconcile/live', response_model=ReconcileRunRead)
async def reconcile_live(db: Session = Depends(db_session)) -> ReconcileRunRead:
    service = OperationsService(db)
    try:
        result = await service.reconcile_live_account()
    except OperationsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ReconcileRunRead(**result)


@router.get('/reconcile/runs', response_model=list[ReconcileRunRead])
def list_reconcile_runs(db: Session = Depends(db_session)) -> list[ReconcileRunRead]:
    return [ReconcileRunRead.model_validate(item, from_attributes=True) for item in OperationsService(db).list_reconcile_runs()]


@router.post('/recovery/run', response_model=RecoveryRunRead)
def run_recovery(db: Session = Depends(db_session)) -> RecoveryRunRead:
    result = OperationsService(db).run_recovery_scan(startup_context='manual')
    return RecoveryRunRead(**result)


@router.get('/recovery/runs', response_model=list[RecoveryRunRead])
def list_recovery_runs(db: Session = Depends(db_session)) -> list[RecoveryRunRead]:
    return [RecoveryRunRead.model_validate(item, from_attributes=True) for item in OperationsService(db).list_recovery_runs()]


@router.post('/flatten-paper', response_model=FlattenPaperResult)
def flatten_paper(db: Session = Depends(db_session)) -> FlattenPaperResult:
    return FlattenPaperResult(**OperationsService(db).flatten_paper_positions())


@router.post('/flatten/live', response_model=FlattenLiveResult)
async def flatten_live(db: Session = Depends(db_session)) -> FlattenLiveResult:
    try:
        return FlattenLiveResult(**(await OperationsService(db).flatten_live_positions(arm_kill_switch=False)))
    except OperationsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/flatten/live/kill-switch', response_model=FlattenLiveResult)
async def flatten_live_kill_switch(db: Session = Depends(db_session)) -> FlattenLiveResult:
    try:
        return FlattenLiveResult(**(await OperationsService(db).flatten_live_positions(arm_kill_switch=True)))
    except OperationsError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/flatten/runs', response_model=list[FlattenRunRead])
def list_flatten_runs(db: Session = Depends(db_session)) -> list[FlattenRunRead]:
    return [FlattenRunRead.model_validate(item, from_attributes=True) for item in OperationsService(db).list_flatten_runs()]
