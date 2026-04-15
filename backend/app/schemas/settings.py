from pydantic import BaseModel, Field


class RuntimeSettingsRead(BaseModel):
    mode: str
    spot_enabled: bool
    futures_enabled: bool
    paper_start_balance: float
    history_start_balance: float
    spot_working_balance: float
    futures_working_balance: float
    notes: str | None = None


class RuntimeSettingsUpdate(BaseModel):
    mode: str = Field(pattern='^(live|paper|historical)$')
    spot_enabled: bool
    futures_enabled: bool
    paper_start_balance: float = Field(ge=0)
    history_start_balance: float = Field(ge=0)
    spot_working_balance: float = Field(ge=0)
    futures_working_balance: float = Field(ge=0)
    notes: str | None = None
