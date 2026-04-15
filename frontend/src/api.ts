import type {
  AnalyticsOverview,
  AnalyticsReview,
  BackupArtifact,
  BackupManifest,
  BacktestRun,
  BacktestRunDetail,
  BacktestRunRequest,
  BalanceOverview,
  BotConfig,
  BotCycleResult,
  BotRun,
  CodexBrowserStart,
  CodexStatus,
  DeepSeekStatus,
  DeepSeekTestResult,
  ExecutionRequest,
  FlattenLiveResult,
  FlattenPaperResult,
  FlattenRun,
  PreflightStatus,
  JournalEntry,
  JournalSummary,
  LifecycleSyncResult,
  LiveLifecycleSyncResult,
  PairSelections,
  PnlOverview,
  ReleaseReadiness,
  PositionLifecycleEvent,
  ReconcileRun,
  RecoveryRun,
  ReleaseAcceptanceRun,
  ReleaseReport,
  RuntimeSettings,
  StrategyDecision,
  StrategyEvaluationRequest,
  StrategyEvaluationResponse,
  StrategyExplanation,
  SymbolItem,
  SystemEvent,
  SystemState,
  TradeOrder,
  TradePosition,
  TradeRecord,
} from './types'

async function parseJson<T>(input: Promise<Response>): Promise<T> {
  const response = await input
  if (!response.ok) {
    let message = `HTTP ${response.status}`
    try {
      const payload = await response.json()
      if (payload?.detail) message = payload.detail
    } catch {
      // ignore
    }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export const api = {
  health: () => parseJson<{ status: string; service: string }>(fetch('/healthz')),
  getSettings: () => parseJson<RuntimeSettings>(fetch('/api/v1/settings/runtime')),
  updateSettings: (payload: RuntimeSettings) =>
    parseJson<RuntimeSettings>(
      fetch('/api/v1/settings/runtime', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  getSpotPairs: () => parseJson<SymbolItem[]>(fetch('/api/v1/pairs/spot')),
  getFuturesPairs: () => parseJson<SymbolItem[]>(fetch('/api/v1/pairs/futures')),
  getSelections: () => parseJson<PairSelections>(fetch('/api/v1/pairs/selections')),
  saveSelections: (payload: PairSelections) =>
    parseJson<PairSelections>(
      fetch('/api/v1/pairs/selections', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  getBalances: () => parseJson<BalanceOverview>(fetch('/api/v1/balances/overview')),
  getCodexStatus: () => parseJson<CodexStatus>(fetch('/api/v1/auth/codex/status')),
  mockConnectCodex: () => parseJson<CodexStatus>(fetch('/api/v1/auth/codex/mock-connect', { method: 'POST' })),
  startCodexBrowserLogin: () => parseJson<CodexBrowserStart>(fetch('/api/v1/auth/codex/browser/start', { method: 'POST' })),
  completeCodexBrowserLogin: (payload: { login_id: string; account_label: string; external_user_id?: string }) =>
    parseJson<CodexStatus>(
      fetch('/api/v1/auth/codex/browser/complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  disconnectCodex: () => parseJson<CodexStatus>(fetch('/api/v1/auth/codex/disconnect', { method: 'POST' })),
  getDeepSeekStatus: () => parseJson<DeepSeekStatus>(fetch('/api/v1/auth/deepseek/status')),
  testDeepSeek: (prompt: string) =>
    parseJson<DeepSeekTestResult>(
      fetch('/api/v1/auth/deepseek/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      }),
    ),
  executeTrade: (payload: ExecutionRequest) =>
    parseJson<Record<string, unknown>>(
      fetch('/api/v1/trade/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  syncPaper: () => parseJson<{ filled_orders: number; closed_positions: number; tracked_symbols: number }>(fetch('/api/v1/trade/paper/sync', { method: 'POST' })),
  syncLive: () => parseJson<Record<string, unknown>>(fetch('/api/v1/trade/live/sync', { method: 'POST' })),
  syncLiveLifecycle: () => parseJson<LiveLifecycleSyncResult>(fetch('/api/v1/trade/live/lifecycle', { method: 'POST' })),
  syncLifecycle: () => parseJson<LifecycleSyncResult>(fetch('/api/v1/trade/lifecycle/sync', { method: 'POST' })),
  getOrders: () => parseJson<TradeOrder[]>(fetch('/api/v1/trade/orders')),
  getTrades: () => parseJson<TradeRecord[]>(fetch('/api/v1/trade/trades')),
  getPositions: () => parseJson<TradePosition[]>(fetch('/api/v1/trade/positions')),
  getLifecycleEvents: () => parseJson<PositionLifecycleEvent[]>(fetch('/api/v1/trade/lifecycle/events')),
  closePosition: (positionId: number) =>
    parseJson<Record<string, unknown>>(
      fetch(`/api/v1/trade/positions/${positionId}/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'manual-close' }),
      }),
    ),
  getPnl: () => parseJson<PnlOverview>(fetch('/api/v1/trade/pnl')),
  getJournal: () => parseJson<JournalEntry[]>(fetch('/api/v1/journal/entries')),
  getJournalSummary: () => parseJson<JournalSummary>(fetch('/api/v1/journal/summary')),
  reviewJournalEntry: (entryId: number) => parseJson<JournalEntry>(fetch(`/api/v1/journal/entries/${entryId}/review`, { method: 'POST' })),
  reviewPendingJournal: (limit = 5) => parseJson<JournalEntry[]>(fetch(`/api/v1/journal/review/pending?limit=${limit}`, { method: 'POST' })),
  getAnalytics: () => parseJson<AnalyticsOverview>(fetch('/api/v1/analytics/overview')),
  reviewAnalytics: () => parseJson<AnalyticsReview>(fetch('/api/v1/analytics/summary/review', { method: 'POST' })),
  getOpsState: () => parseJson<SystemState>(fetch('/api/v1/ops/state')),
  getPreflight: () => parseJson<PreflightStatus>(fetch('/api/v1/ops/preflight')),
  getReleaseReadiness: () => parseJson<ReleaseReadiness>(fetch('/api/v1/ops/release-readiness')),
  getBackupArtifacts: () => parseJson<BackupArtifact[]>(fetch('/api/v1/ops/backups')),
  createBackupManifest: () => parseJson<BackupManifest>(fetch('/api/v1/ops/backup/manifest', { method: 'POST' })),

  getReleaseArtifacts: () => parseJson<BackupArtifact[]>(fetch('/api/v1/ops/releases')),
  getReleaseReport: () => parseJson<ReleaseReport>(fetch('/api/v1/ops/release-report')),
  runReleaseAcceptance: () => parseJson<ReleaseAcceptanceRun>(fetch('/api/v1/ops/release-acceptance/run', { method: 'POST' })),
  updateOpsState: (payload: SystemState) =>
    parseJson<SystemState>(
      fetch('/api/v1/ops/state', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          maintenance_mode: payload.maintenance_mode,
          trading_paused: payload.trading_paused,
          kill_switch_armed: payload.kill_switch_armed,
        }),
      }),
    ),
  reconcileLive: () => parseJson<ReconcileRun>(fetch('/api/v1/ops/reconcile/live', { method: 'POST' })),
  getReconcileRuns: () => parseJson<ReconcileRun[]>(fetch('/api/v1/ops/reconcile/runs')),
  runRecovery: () => parseJson<RecoveryRun>(fetch('/api/v1/ops/recovery/run', { method: 'POST' })),
  getRecoveryRuns: () => parseJson<RecoveryRun[]>(fetch('/api/v1/ops/recovery/runs')),
  flattenPaper: () => parseJson<FlattenPaperResult>(fetch('/api/v1/ops/flatten-paper', { method: 'POST' })),
  flattenLive: () => parseJson<FlattenLiveResult>(fetch('/api/v1/ops/flatten/live', { method: 'POST' })),
  flattenLiveKillSwitch: () => parseJson<FlattenLiveResult>(fetch('/api/v1/ops/flatten/live/kill-switch', { method: 'POST' })),
  getFlattenRuns: () => parseJson<FlattenRun[]>(fetch('/api/v1/ops/flatten/runs')),
  getBotConfig: () => parseJson<BotConfig>(fetch('/api/v1/bot/config')),
  updateBotConfig: (payload: BotConfig) =>
    parseJson<BotConfig>(
      fetch('/api/v1/bot/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  runBotCycle: () => parseJson<BotCycleResult>(fetch('/api/v1/bot/cycle', { method: 'POST' })),
  getBotRuns: () => parseJson<BotRun[]>(fetch('/api/v1/bot/runs')),
  getBotEvents: () => parseJson<SystemEvent[]>(fetch('/api/v1/bot/events')),
  evaluateStrategy: (payload: StrategyEvaluationRequest) =>
    parseJson<StrategyEvaluationResponse>(
      fetch('/api/v1/strategy/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  getStrategyDecisions: () => parseJson<StrategyDecision[]>(fetch('/api/v1/strategy/decisions')),
  explainStrategyDecision: (decisionId: number) => parseJson<StrategyExplanation>(fetch(`/api/v1/strategy/decisions/${decisionId}/explain`, { method: 'POST' })),
  runBacktest: (payload: BacktestRunRequest) =>
    parseJson<BacktestRun>(
      fetch('/api/v1/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      }),
    ),
  getBacktestRuns: () => parseJson<BacktestRun[]>(fetch('/api/v1/backtest/runs')),
  getBacktestRun: (runId: number) => parseJson<BacktestRunDetail>(fetch(`/api/v1/backtest/runs/${runId}`)),
}
