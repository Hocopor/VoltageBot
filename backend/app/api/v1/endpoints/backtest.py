from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.backtest import BacktestRunDetail, BacktestRunRead, BacktestRunRequest, BacktestTradeRead
from app.services.backtest import BacktestService

router = APIRouter()


@router.post('/run', response_model=BacktestRunRead)
async def run_backtest(payload: BacktestRunRequest, db: Session = Depends(db_session)) -> BacktestRunRead:
    run = await BacktestService(db).run(
        payload.symbol,
        payload.market_type,
        payload.timeframe,
        payload.candles,
        payload.start_balance,
        payload.side_policy,
    )
    return BacktestRunRead.model_validate(run, from_attributes=True)


@router.get('/runs', response_model=list[BacktestRunRead])
def list_runs(db: Session = Depends(db_session)) -> list[BacktestRunRead]:
    return [BacktestRunRead.model_validate(item, from_attributes=True) for item in BacktestService(db).list_runs()]


@router.get('/runs/{run_id}', response_model=BacktestRunDetail)
def get_run(run_id: int, db: Session = Depends(db_session)) -> BacktestRunDetail:
    run, trades = BacktestService(db).get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail='Прогон бэктеста не найден.')
    return BacktestRunDetail(
        **BacktestRunRead.model_validate(run, from_attributes=True).model_dump(),
        trades=[BacktestTradeRead.model_validate(item, from_attributes=True) for item in trades],
    )
