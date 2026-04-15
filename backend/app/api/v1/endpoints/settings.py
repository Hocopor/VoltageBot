from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models.account import RuntimeSetting
from app.schemas.settings import RuntimeSettingsRead, RuntimeSettingsUpdate

router = APIRouter()


@router.get('/runtime', response_model=RuntimeSettingsRead)
def read_runtime_settings(db: Session = Depends(db_session)) -> RuntimeSettingsRead:
    settings = db.query(RuntimeSetting).order_by(RuntimeSetting.id.asc()).first()
    if not settings:
        raise HTTPException(status_code=404, detail='Runtime settings not initialized')
    return RuntimeSettingsRead(
        mode=settings.mode,
        spot_enabled=settings.spot_enabled,
        futures_enabled=settings.futures_enabled,
        paper_start_balance=settings.paper_start_balance,
        history_start_balance=settings.history_start_balance,
        spot_working_balance=settings.spot_working_balance,
        futures_working_balance=settings.futures_working_balance,
        notes=settings.notes,
    )


@router.put('/runtime', response_model=RuntimeSettingsRead)
def update_runtime_settings(payload: RuntimeSettingsUpdate, db: Session = Depends(db_session)) -> RuntimeSettingsRead:
    settings = db.query(RuntimeSetting).order_by(RuntimeSetting.id.asc()).first()
    if not settings:
        settings = RuntimeSetting()
        db.add(settings)
    settings.mode = payload.mode
    settings.spot_enabled = payload.spot_enabled
    settings.futures_enabled = payload.futures_enabled
    settings.paper_start_balance = payload.paper_start_balance
    settings.history_start_balance = payload.history_start_balance
    settings.spot_working_balance = payload.spot_working_balance
    settings.futures_working_balance = payload.futures_working_balance
    settings.notes = payload.notes
    db.commit()
    db.refresh(settings)
    return RuntimeSettingsRead(
        mode=settings.mode,
        spot_enabled=settings.spot_enabled,
        futures_enabled=settings.futures_enabled,
        paper_start_balance=settings.paper_start_balance,
        history_start_balance=settings.history_start_balance,
        spot_working_balance=settings.spot_working_balance,
        futures_working_balance=settings.futures_working_balance,
        notes=settings.notes,
    )
