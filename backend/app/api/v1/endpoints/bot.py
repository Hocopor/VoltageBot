from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.bot import BotConfigRead, BotConfigUpdate, BotCycleResult, BotRunRead, SystemEventRead
from app.services.bot_runtime import BotRuntimeService

router = APIRouter()


@router.get('/config', response_model=BotConfigRead)
def read_bot_config(db: Session = Depends(db_session)) -> BotConfigRead:
    item = BotRuntimeService(db).get_config()
    return BotConfigRead(
        enabled=item.enabled,
        auto_execute=item.auto_execute,
        live_execution_allowed=item.live_execution_allowed,
        scan_interval_seconds=item.scan_interval_seconds,
        strategy_timeframe=item.strategy_timeframe,
        strategy_candles=item.strategy_candles,
        risk_percent=item.risk_percent,
        max_new_positions_per_cycle=item.max_new_positions_per_cycle,
        notes=item.notes,
        last_cycle_started_at=item.last_cycle_started_at,
        last_cycle_finished_at=item.last_cycle_finished_at,
        last_cycle_status=item.last_cycle_status,
        last_cycle_summary=item.last_cycle_summary,
        last_error=item.last_error,
    )


@router.put('/config', response_model=BotConfigRead)
def update_bot_config(payload: BotConfigUpdate, db: Session = Depends(db_session)) -> BotConfigRead:
    item = BotRuntimeService(db).update_config(payload)
    return BotConfigRead(
        enabled=item.enabled,
        auto_execute=item.auto_execute,
        live_execution_allowed=item.live_execution_allowed,
        scan_interval_seconds=item.scan_interval_seconds,
        strategy_timeframe=item.strategy_timeframe,
        strategy_candles=item.strategy_candles,
        risk_percent=item.risk_percent,
        max_new_positions_per_cycle=item.max_new_positions_per_cycle,
        notes=item.notes,
        last_cycle_started_at=item.last_cycle_started_at,
        last_cycle_finished_at=item.last_cycle_finished_at,
        last_cycle_status=item.last_cycle_status,
        last_cycle_summary=item.last_cycle_summary,
        last_error=item.last_error,
    )


@router.post('/cycle', response_model=BotCycleResult)
async def run_bot_cycle(db: Session = Depends(db_session)) -> BotCycleResult:
    return BotCycleResult(**(await BotRuntimeService(db).run_cycle(trigger_type='manual', ignore_enabled_flag=True)))


@router.get('/runs', response_model=list[BotRunRead])
def list_runs(db: Session = Depends(db_session)) -> list[BotRunRead]:
    return [BotRunRead.model_validate(item, from_attributes=True) for item in BotRuntimeService(db).list_runs()]


@router.get('/events', response_model=list[SystemEventRead])
def list_events(db: Session = Depends(db_session)) -> list[SystemEventRead]:
    return [SystemEventRead.model_validate(item, from_attributes=True) for item in BotRuntimeService(db).list_events()]
