from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models.strategy import StrategyDecision
from app.schemas.strategy import (
    StrategyDecisionRead,
    StrategyEvaluateRequest,
    StrategyEvaluateResponse,
    StrategyExplanationRead,
    StrategyRegistryItem,
)
from app.services.ai_review import AIReviewService
from app.services.strategy_engine import StrategyEngineService
from app.services.strategy_registry import StrategyRegistry

router = APIRouter()


@router.get('/voltage', response_model=StrategyRegistryItem)
def get_voltage_strategy() -> StrategyRegistryItem:
    item = StrategyRegistry().get_voltage()
    return StrategyRegistryItem(
        name=item['name'],
        version=item['version'],
        immutable=item['immutable'],
        text=item['text'],
    )


@router.post('/evaluate', response_model=StrategyEvaluateResponse)
async def evaluate_strategy(payload: StrategyEvaluateRequest, db: Session = Depends(db_session)) -> StrategyEvaluateResponse:
    signal = await StrategyEngineService(db).evaluate(payload.symbol, payload.market_type, payload.side, timeframe=payload.timeframe, candles=payload.candles)
    db.commit()
    return StrategyEvaluateResponse(
        symbol=signal.symbol,
        market_type=signal.market_type,
        side=signal.side,
        allowed=signal.allowed,
        market_scenario=signal.market_scenario,
        confidence=signal.confidence,
        entry_price=signal.entry_price,
        stop_loss=signal.stop_loss,
        take_profit_1=signal.take_profit_1,
        take_profit_2=signal.take_profit_2,
        take_profit_3=signal.take_profit_3,
        filter_summary=signal.filter_summary,
        risk_summary=signal.risk_summary,
        created_decision_id=signal.decision_id,
    )


@router.get('/decisions', response_model=list[StrategyDecisionRead])
def list_decisions(db: Session = Depends(db_session)) -> list[StrategyDecisionRead]:
    return [StrategyDecisionRead.model_validate(item, from_attributes=True) for item in StrategyEngineService(db).list_decisions()]


@router.post('/decisions/{decision_id}/explain', response_model=StrategyExplanationRead)
async def explain_decision(decision_id: int, db: Session = Depends(db_session)) -> StrategyExplanationRead:
    decision = db.get(StrategyDecision, decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail='Strategy decision not found')
    status, explanation = await AIReviewService().explain_strategy_decision(decision)
    return StrategyExplanationRead(decision_id=decision.id, status=status, explanation=explanation)
