from datetime import datetime

from pydantic import BaseModel


class SystemStateRead(BaseModel):
    maintenance_mode: bool
    trading_paused: bool
    kill_switch_armed: bool
    boot_count: int
    last_startup_at: str | None = None
    last_shutdown_at: str | None = None
    last_bot_heartbeat_at: str | None = None
    last_reconcile_at: str | None = None
    last_lifecycle_sync_at: str | None = None
    last_live_sync_status: str | None = None
    last_live_sync_message: str | None = None
    recovery_runs_count: int = 0
    last_recovery_at: str | None = None
    last_flatten_at: str | None = None
    last_flatten_status: str | None = None
    last_flatten_message: str | None = None
    open_positions: int = 0
    open_live_positions: int = 0
    open_paper_positions: int = 0


class SystemControlsUpdate(BaseModel):
    maintenance_mode: bool
    trading_paused: bool
    kill_switch_armed: bool


class ReconcileRunRead(BaseModel):
    id: int
    source: str
    status: str
    balances_synced: int
    orders_seen: int
    positions_seen: int
    closed_local_positions: int
    summary: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: datetime


class RecoveryRunRead(BaseModel):
    id: int
    startup_context: str
    status: str
    stale_bot_runs: int
    recovered_positions: int
    summary: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: datetime


class FlattenPaperResult(BaseModel):
    closed_positions: int
    status: str


class FlattenLiveResult(BaseModel):
    run_id: int
    mode: str
    scope: str
    status: str
    orders_cancelled: int
    close_orders_submitted: int
    symbols_touched: int
    summary: str | None = None


class FlattenRunRead(BaseModel):
    id: int
    mode: str
    scope: str
    status: str
    orders_cancelled: int
    close_orders_submitted: int
    symbols_touched: int
    summary: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    created_at: datetime


class PreflightCheckRead(BaseModel):
    name: str
    status: str
    message: str


class PreflightRead(BaseModel):
    generated_at: str
    environment: str
    database_scheme: str
    redis_scheme: str
    backup_root: str
    release_root: str
    codex_session_dir: str
    cloudflare_configured: bool
    checks: list[PreflightCheckRead]
    overall_status: str


class ReleaseCountsRead(BaseModel):
    orders: int
    trades: int
    positions: int
    journal_entries: int


class ReleaseReadinessRead(BaseModel):
    generated_at: str
    score: int
    ready_for_paper: bool
    ready_for_live: bool
    critical_issues: list[str]
    warnings: list[str]
    preflight_status: str
    counts: ReleaseCountsRead
    state: SystemStateRead | None = None


class BackupArtifactRead(BaseModel):
    name: str
    path: str
    size_bytes: int
    modified_at: str
    kind: str


class BackupManifestRead(BaseModel):
    name: str
    path: str
    size_bytes: int
    sha256: str
    generated_at: str
    source: str


class AcceptanceCheckRead(BaseModel):
    name: str
    status: str
    message: str


class ReleaseReportRead(BaseModel):
    generated_at: str
    project: str
    version: str
    environment: str
    preflight: PreflightRead
    readiness: ReleaseReadinessRead
    codex: dict
    deepseek: dict
    state: SystemStateRead
    acceptance_checks: list[AcceptanceCheckRead]
    overall_status: str
    recommended_mode: str
    journal_entries: int
    bot_runs: int
    system_events: int
    backup_artifacts: list[BackupArtifactRead]
    release_artifacts: list[BackupArtifactRead]
    next_actions: list[str]


class ReleaseAcceptanceRunRead(BaseModel):
    generated_at: str
    overall_status: str
    recommended_mode: str
    score: int
    ready_for_paper: bool
    ready_for_live: bool
    json_artifact: BackupArtifactRead
    markdown_artifact: BackupArtifactRead
    critical_issues: list[str]
    warnings: list[str]
    next_actions: list[str]
