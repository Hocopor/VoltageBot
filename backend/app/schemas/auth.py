from pydantic import BaseModel, Field


class CodexStatusRead(BaseModel):
    connected: bool
    mode: str
    message: str
    account_label: str | None = None
    session_id: str | None = None
    connected_at: str | None = None
    last_sync_at: str | None = None
    pending_login: bool = False
    pending_login_id: str | None = None
    expires_at: str | None = None


class CodexBrowserStartRead(BaseModel):
    login_id: str
    mode: str
    auth_url: str
    callback_path: str
    expires_at: str
    message: str


class CodexBrowserCompleteRequest(BaseModel):
    login_id: str
    account_label: str = Field(min_length=1, max_length=120)
    external_user_id: str | None = Field(default=None, max_length=120)


class DeepSeekStatusRead(BaseModel):
    configured: bool
    model: str
    base_url: str
    message: str


class DeepSeekTestRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=2000)


class DeepSeekTestRead(BaseModel):
    status: str
    model: str
    text: str
