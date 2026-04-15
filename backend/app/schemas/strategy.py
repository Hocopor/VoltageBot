from datetime import datetime

from pydantic import BaseModel, Field


class StrategyRegistryItem(BaseModel):
    name: str
    version: str
    immutable: bool
    text: str


class StrategyDecisionRead(BaseModel):
    id: int
    strategy_name: str
    symbol: str
    timeframe_context: str
    allowed: bool
    market_scenario: str | None
    filter_summary: str | None
    risk_summary: str | None
    confidence: float
    created_at: datetime


class StrategyEvaluateRequest(BaseModel):
    symbol: str = Field(min_length=3)
    market_type: str = Field(pattern='^(spot|futures)$')
    side: str = Field(pattern='^(buy|sell)$')
    timeframe: str = '1H'
    candles: int = Field(default=240, ge=120, le=1000)


class StrategyEvaluateResponse(BaseModel):
    symbol: str
    market_type: str
    side: str
    allowed: bool
    market_scenario: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    filter_summary: str
    risk_summary: str
    created_decision_id: int


class StrategyExplanationRead(BaseModel):
    decision_id: int
    status: str
    explanation: str
