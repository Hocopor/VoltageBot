from fastapi import APIRouter, HTTPException, Query, Request, Response

from app.schemas.auth import (
    CodexBrowserCompleteRequest,
    CodexBrowserStartRead,
    CodexStatusRead,
    DeepSeekStatusRead,
    DeepSeekTestRead,
    DeepSeekTestRequest,
    LoginRequest,
    SessionStatusRead,
)
from app.services.admin_auth import AdminAuthError, AdminAuthService
from app.services.codex_auth import CodexAuthError, CodexAuthService
from app.services.deepseek import DeepSeekClient

router = APIRouter()


@router.get('/session', response_model=SessionStatusRead)
def auth_session(request: Request) -> SessionStatusRead:
    session = AdminAuthService().read_session(request.cookies.get(AdminAuthService().session_cookie_name()))
    if not session:
        return SessionStatusRead(authenticated=False, message='Требуется вход в систему.')
    return SessionStatusRead(**session, message='Сессия активна.')


@router.post('/login', response_model=SessionStatusRead)
def login(payload: LoginRequest, response: Response) -> SessionStatusRead:
    service = AdminAuthService()
    try:
        token = service.login(payload.username, payload.password)
    except AdminAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    session = service.read_session(token)
    response.set_cookie(
        key=service.session_cookie_name(),
        value=token,
        httponly=True,
        secure=service.cookie_is_secure(),
        samesite='lax',
        max_age=service.settings.auth_session_ttl_hours * 3600,
        path='/',
    )
    return SessionStatusRead(**(session or {'authenticated': True, 'username': payload.username}), message='Вход выполнен.')


@router.post('/logout', response_model=SessionStatusRead)
def logout(response: Response) -> SessionStatusRead:
    service = AdminAuthService()
    response.delete_cookie(key=service.session_cookie_name(), path='/')
    return SessionStatusRead(authenticated=False, message='Вы вышли из системы.')


@router.get('/codex/status', response_model=CodexStatusRead)
def codex_status() -> CodexStatusRead:
    return CodexStatusRead(**CodexAuthService().status())


@router.post('/codex/mock-connect', response_model=CodexStatusRead)
def codex_mock_connect() -> CodexStatusRead:
    return CodexStatusRead(**CodexAuthService().save_placeholder_session('chatgpt-linked-user'))


@router.post('/codex/browser/start', response_model=CodexBrowserStartRead)
def codex_browser_start() -> CodexBrowserStartRead:
    return CodexBrowserStartRead(**CodexAuthService().start_browser_login())


@router.post('/codex/browser/complete', response_model=CodexStatusRead)
def codex_browser_complete(payload: CodexBrowserCompleteRequest) -> CodexStatusRead:
    try:
        result = CodexAuthService().complete_browser_login(
            login_id=payload.login_id,
            account_label=payload.account_label,
            external_user_id=payload.external_user_id,
        )
    except CodexAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CodexStatusRead(**result)


@router.get('/codex/browser/callback', response_model=CodexStatusRead)
def codex_browser_callback(login_id: str = Query(...), account_label: str | None = Query(default=None)) -> CodexStatusRead:
    try:
        result = CodexAuthService().complete_browser_callback(login_id=login_id, account_label=account_label)
    except CodexAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CodexStatusRead(**result)


@router.post('/codex/disconnect', response_model=CodexStatusRead)
def codex_disconnect() -> CodexStatusRead:
    return CodexStatusRead(**CodexAuthService().disconnect())


@router.get('/deepseek/status', response_model=DeepSeekStatusRead)
def deepseek_status() -> DeepSeekStatusRead:
    return DeepSeekStatusRead(**DeepSeekClient().status())


@router.post('/deepseek/test', response_model=DeepSeekTestRead)
async def deepseek_test(payload: DeepSeekTestRequest) -> DeepSeekTestRead:
    return DeepSeekTestRead(**(await DeepSeekClient().test_prompt(payload.prompt)))
