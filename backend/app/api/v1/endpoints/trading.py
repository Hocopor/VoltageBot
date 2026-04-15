from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.trading import (
    ExecutionRequest,
    LifecycleSyncRead,
    LiveLifecycleSyncRead,
    OrderRead,
    PnlOverviewRead,
    PositionCloseRequest,
    PositionLifecycleEventRead,
    PositionRead,
    SyncRead,
    TradeRead,
)
from app.services.bybit import BybitError
from app.services.trading import TradingError, TradingService

router = APIRouter()


def _order_read(item) -> OrderRead:
    return OrderRead(
        id=item.id,
        mode=item.mode,
        market_type=item.market_type,
        symbol=item.symbol,
        side=item.side,
        order_type=item.order_type,
        stage=item.stage,
        status=item.status,
        qty=item.qty,
        filled_qty=item.filled_qty,
        price=item.price,
        avg_fill_price=item.avg_fill_price,
        stop_loss=item.stop_loss,
        take_profit_1=item.take_profit_1,
        take_profit_2=item.take_profit_2,
        take_profit_3=item.take_profit_3,
        reduce_only=item.reduce_only,
        last_exchange_status=item.last_exchange_status,
        last_exchange_update_at=item.last_exchange_update_at,
        created_at=item.created_at,
    )


def _trade_read(item) -> TradeRead:
    return TradeRead(
        id=item.id,
        mode=item.mode,
        market_type=item.market_type,
        symbol=item.symbol,
        direction=item.direction,
        status=item.status,
        entry_price=item.entry_price,
        exit_price=item.exit_price,
        initial_qty=item.initial_qty,
        remaining_qty=item.remaining_qty,
        stop_loss=item.stop_loss,
        take_profit_1=item.take_profit_1,
        take_profit_2=item.take_profit_2,
        take_profit_3=item.take_profit_3,
        realized_pnl=item.realized_pnl,
        unrealized_pnl=item.unrealized_pnl,
        created_at=item.created_at,
    )


def _position_read(item) -> PositionRead:
    return PositionRead(
        id=item.id,
        trade_id=item.trade_id,
        mode=item.mode,
        market_type=item.market_type,
        symbol=item.symbol,
        side=item.side,
        status=item.status,
        size=item.size,
        initial_size=item.initial_size,
        avg_entry_price=item.avg_entry_price,
        mark_price=item.mark_price,
        stop_loss=item.stop_loss,
        take_profit_1=item.take_profit_1,
        take_profit_2=item.take_profit_2,
        take_profit_3=item.take_profit_3,
        tp1_hit=item.tp1_hit,
        tp2_hit=item.tp2_hit,
        tp3_hit=item.tp3_hit,
        trailing_active=item.trailing_active,
        best_price=item.best_price,
        worst_price=item.worst_price,
        position_idx=item.position_idx,
        last_exchange_size=item.last_exchange_size,
        last_live_sync_at=item.last_live_sync_at,
        external_source=item.external_source,
        created_at=item.created_at,
    )


@router.post('/execute')
async def execute_trade(payload: ExecutionRequest, db: Session = Depends(db_session)) -> dict:
    try:
        return await TradingService(db).execute_trade(payload)
    except (TradingError, BybitError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/paper/sync', response_model=SyncRead)
async def sync_paper_market(db: Session = Depends(db_session)) -> SyncRead:
    return SyncRead(**(await TradingService(db).sync_paper_market()))


@router.post('/live/sync')
async def sync_live_account(db: Session = Depends(db_session)) -> dict:
    try:
        return await TradingService(db).sync_live_account()
    except (TradingError, BybitError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/live/lifecycle', response_model=LiveLifecycleSyncRead)
async def sync_live_lifecycle(db: Session = Depends(db_session)) -> LiveLifecycleSyncRead:
    try:
        return LiveLifecycleSyncRead(**(await TradingService(db).sync_live_lifecycle()))
    except (TradingError, BybitError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/lifecycle/sync', response_model=LifecycleSyncRead)
async def sync_lifecycle(db: Session = Depends(db_session)) -> LifecycleSyncRead:
    return LifecycleSyncRead(**(await TradingService(db).sync_lifecycle()))


@router.post('/positions/{position_id}/close')
def close_position(position_id: int, payload: PositionCloseRequest, db: Session = Depends(db_session)) -> dict:
    try:
        return TradingService(db).close_position(position_id, payload.exit_price, payload.reason)
    except TradingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/orders', response_model=list[OrderRead])
def list_orders(db: Session = Depends(db_session)) -> list[OrderRead]:
    return [_order_read(item) for item in TradingService(db).list_orders()]


@router.get('/trades', response_model=list[TradeRead])
def list_trades(db: Session = Depends(db_session)) -> list[TradeRead]:
    return [_trade_read(item) for item in TradingService(db).list_trades()]


@router.get('/positions', response_model=list[PositionRead])
def list_positions(db: Session = Depends(db_session)) -> list[PositionRead]:
    return [_position_read(item) for item in TradingService(db).list_positions()]


@router.get('/lifecycle/events', response_model=list[PositionLifecycleEventRead])
def list_lifecycle_events(db: Session = Depends(db_session)) -> list[PositionLifecycleEventRead]:
    return [PositionLifecycleEventRead.model_validate(item, from_attributes=True) for item in TradingService(db).list_lifecycle_events()]


@router.get('/pnl', response_model=PnlOverviewRead)
def pnl_overview(db: Session = Depends(db_session)) -> PnlOverviewRead:
    return PnlOverviewRead(**TradingService(db).pnl_overview())
