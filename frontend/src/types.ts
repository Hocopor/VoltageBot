export type RuntimeSettings = {
  mode: 'live' | 'paper' | 'historical'
  spot_enabled: boolean
  futures_enabled: boolean
  paper_start_balance: number
  history_start_balance: number
  spot_working_balance: number
  futures_working_balance: number
  notes?: string | null
}

export type SymbolItem = {
  symbol: string
  market_type: string
}

export type PairSelections = {
  spot_symbols: string[]
  futures_symbols: string[]
}

export type BalanceItem = {
  asset: string
  total: number
  available: number
  usd_value: number
  market_type: string
}

export type BalanceOverview = {
  mode: string
  total_wallet_usd: number
  spot_working_balance: number
  futures_working_balance: number
  balances: BalanceItem[]
}

export type ExecutionRequest = {
  symbol: string
  market_type: 'spot' | 'futures'
  side: 'buy' | 'sell'
  order_type: 'market' | 'limit'
  qty?: number
  price?: number
  stop_loss?: number
  risk_percent: number
  note?: string
}

export type TradeOrder = {
  id: number
  mode: string
  market_type: string
  symbol: string
  side: string
  order_type: string
  stage: string
  status: string
  qty: number
  filled_qty: number
  price?: number | null
  avg_fill_price?: number | null
  stop_loss?: number | null
  take_profit_1?: number | null
  take_profit_2?: number | null
  take_profit_3?: number | null
  reduce_only?: boolean
  last_exchange_status?: string | null
  last_exchange_update_at?: string | null
  created_at: string
}

export type TradePosition = {
  id: number
  trade_id?: number | null
  mode: string
  market_type: string
  symbol: string
  side: string
  status: string
  size: number
  initial_size: number
  avg_entry_price: number
  mark_price?: number | null
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  tp1_hit: boolean
  tp2_hit: boolean
  tp3_hit: boolean
  trailing_active: boolean
  best_price?: number | null
  worst_price?: number | null
  position_idx?: number
  last_exchange_size?: number | null
  last_live_sync_at?: string | null
  external_source?: string | null
  created_at: string
}

export type PositionLifecycleEvent = {
  id: number
  position_id?: number | null
  trade_id?: number | null
  mode: string
  market_type: string
  symbol: string
  side: string
  event_type: string
  message: string
  price?: number | null
  payload_json?: string | null
  created_at: string
}

export type LifecycleSyncResult = {
  synced_positions: number
  closed_positions: number
  created_events: number
}

export type LiveLifecycleSyncResult = {
  orders_checked: number
  orders_updated: number
  orders_filled: number
  orders_cancelled: number
  positions_seen: number
  positions_adopted: number
  positions_closed: number
  protections_applied: number
  created_events: number
  summary: string
}

export type TradeRecord = {
  id: number
  mode: string
  market_type: string
  symbol: string
  direction: string
  status: string
  entry_price: number
  exit_price?: number | null
  initial_qty: number
  remaining_qty: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  realized_pnl: number
  unrealized_pnl: number
  created_at: string
}

export type PnlOverview = {
  realized_pnl: number
  unrealized_pnl: number
  open_positions: number
  closed_trades: number
  win_rate: number
}

export type JournalEntry = {
  id: number
  trade_id?: number | null
  backtest_run_id?: number | null
  mode: string
  market_type: string
  symbol: string
  direction: string
  quantity: number
  entry_price: number
  exit_price?: number | null
  stop_loss?: number | null
  take_profit_1?: number | null
  take_profit_2?: number | null
  take_profit_3?: number | null
  realized_pnl: number
  entry_index?: number | null
  exit_index?: number | null
  chart_points?: string | null
  tags?: string | null
  ai_review_status: string
  ai_review_text?: string | null
  close_reason?: string | null
  hold_minutes?: number | null
  best_price?: number | null
  worst_price?: number | null
  mfe_pnl?: number | null
  mae_pnl?: number | null
  strategy_scenario?: string | null
  compliance_score?: number | null
  review_summary?: string | null
  created_at: string
}

export type JournalSummary = {
  total_entries: number
  total_realized_pnl: number
  wins: number
  losses: number
  avg_hold_minutes: number
  by_mode: Record<string, number>
}

export type AnalyticsOverview = {
  total_trades: number
  closed_trades: number
  realized_pnl: number
  profit_factor: number
  average_rr: number
  max_drawdown: number
  by_mode: Record<string, number>
  by_market: Record<string, number>
  by_symbol: Record<string, number>
  by_direction: Record<string, number>
  by_close_reason: Record<string, number>
  by_weekday: Record<string, number>
  by_hour: Record<string, number>
  monthly_pnl: Record<string, number>
  yearly_pnl: Record<string, number>
  tp_hit_distribution: Record<string, number>
  streaks: Record<string, number>
  average_hold_minutes: number
  average_compliance_score: number
  recent_equity_curve: number[]
}

export type StrategyDecision = {
  id: number
  strategy_name: string
  symbol: string
  timeframe_context: string
  allowed: boolean
  market_scenario?: string | null
  filter_summary?: string | null
  risk_summary?: string | null
  confidence: number
  created_at: string
}

export type StrategyEvaluationRequest = {
  symbol: string
  market_type: 'spot' | 'futures'
  side: 'buy' | 'sell'
  timeframe: string
  candles: number
}

export type StrategyEvaluationResponse = {
  symbol: string
  market_type: string
  side: string
  allowed: boolean
  market_scenario: string
  confidence: number
  entry_price: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  filter_summary: string
  risk_summary: string
  created_decision_id: number
}

export type BacktestRunRequest = {
  symbol: string
  market_type: 'spot' | 'futures'
  timeframe: string
  candles: number
  start_balance: number
  side_policy: 'long_only' | 'short_only' | 'both'
}

export type BacktestTrade = {
  id: number
  run_id: number
  symbol: string
  market_type: string
  direction: string
  entry_index: number
  exit_index: number
  entry_price: number
  exit_price: number
  quantity: number
  stop_loss: number
  take_profit_1: number
  take_profit_2: number
  take_profit_3: number
  realized_pnl: number
  rr_multiple: number
  close_reason: string
  notes?: string | null
  created_at: string
}

export type BacktestRun = {
  id: number
  mode: string
  market_type: string
  symbol: string
  timeframe: string
  candles: number
  start_balance: number
  end_balance: number
  total_trades: number
  closed_trades: number
  wins: number
  losses: number
  win_rate: number
  realized_pnl: number
  max_drawdown: number
  profit_factor: number
  average_rr: number
  target_metrics_met: boolean
  notes?: string | null
  created_at: string
}

export type BacktestRunDetail = BacktestRun & { trades: BacktestTrade[] }

export type BotConfig = {
  enabled: boolean
  auto_execute: boolean
  live_execution_allowed: boolean
  scan_interval_seconds: number
  strategy_timeframe: '15M' | '1H' | '4H' | '1D'
  strategy_candles: number
  risk_percent: number
  max_new_positions_per_cycle: number
  notes?: string | null
  last_cycle_started_at?: string | null
  last_cycle_finished_at?: string | null
  last_cycle_status?: string | null
  last_cycle_summary?: string | null
  last_error?: string | null
}

export type BotRun = {
  id: number
  mode: string
  status: string
  trigger_type: string
  scanned_pairs: number
  decisions_total: number
  allowed_total: number
  executed_total: number
  skipped_total: number
  errors_total: number
  summary?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at: string
}

export type SystemEvent = {
  id: number
  level: string
  source: string
  event_type: string
  message: string
  related_symbol?: string | null
  related_market_type?: string | null
  bot_run_id?: number | null
  payload_json?: string | null
  created_at: string
}

export type BotCycleResult = {
  run_id: number
  mode: string
  status: string
  scanned_pairs: number
  decisions_total: number
  allowed_total: number
  executed_total: number
  skipped_total: number
  errors_total: number
  summary: string
}

export type SystemState = {
  maintenance_mode: boolean
  trading_paused: boolean
  kill_switch_armed: boolean
  boot_count: number
  last_startup_at?: string | null
  last_shutdown_at?: string | null
  last_bot_heartbeat_at?: string | null
  last_reconcile_at?: string | null
  last_lifecycle_sync_at?: string | null
  last_live_sync_status?: string | null
  last_live_sync_message?: string | null
  recovery_runs_count: number
  last_recovery_at?: string | null
  last_flatten_at?: string | null
  last_flatten_status?: string | null
  last_flatten_message?: string | null
  open_positions: number
  open_live_positions: number
  open_paper_positions: number
}


export type PreflightCheck = {
  name: string
  status: string
  message: string
}

export type PreflightStatus = {
  generated_at: string
  environment: string
  database_scheme: string
  redis_scheme: string
  backup_root: string
  release_root: string
  codex_session_dir: string
  cloudflare_configured: boolean
  checks: PreflightCheck[]
  overall_status: string
}

export type ReleaseCounts = {
  orders: number
  trades: number
  positions: number
  journal_entries: number
}

export type ReleaseReadiness = {
  generated_at: string
  score: number
  ready_for_paper: boolean
  ready_for_live: boolean
  critical_issues: string[]
  warnings: string[]
  preflight_status: string
  counts: ReleaseCounts
  state?: SystemState | null
}

export type BackupArtifact = {
  name: string
  path: string
  size_bytes: number
  modified_at: string
  kind: string
}

export type BackupManifest = {
  name: string
  path: string
  size_bytes: number
  sha256: string
  generated_at: string
  source: string
}

export type ReconcileRun = {
  id: number
  source: string
  status: string
  balances_synced: number
  orders_seen: number
  positions_seen: number
  closed_local_positions: number
  summary?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at: string
}

export type RecoveryRun = {
  id: number
  startup_context: string
  status: string
  stale_bot_runs: number
  recovered_positions: number
  summary?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at: string
}

export type FlattenPaperResult = {
  closed_positions: number
  status: string
}


export type FlattenLiveResult = {
  run_id: number
  mode: string
  scope: string
  status: string
  orders_cancelled: number
  close_orders_submitted: number
  symbols_touched: number
  summary?: string | null
}

export type FlattenRun = {
  id: number
  mode: string
  scope: string
  status: string
  orders_cancelled: number
  close_orders_submitted: number
  symbols_touched: number
  summary?: string | null
  started_at?: string | null
  finished_at?: string | null
  created_at: string
}


export type CodexStatus = {
  connected: boolean
  mode: string
  message: string
  account_label?: string | null
  session_id?: string | null
  connected_at?: string | null
  last_sync_at?: string | null
  pending_login: boolean
  pending_login_id?: string | null
  expires_at?: string | null
}

export type CodexBrowserStart = {
  login_id: string
  mode: string
  auth_url: string
  callback_path: string
  expires_at: string
  message: string
}

export type DeepSeekStatus = {
  configured: boolean
  model: string
  base_url: string
  message: string
}

export type DeepSeekTestResult = {
  status: string
  model: string
  text: string
}

export type StrategyExplanation = {
  decision_id: number
  status: string
  explanation: string
}

export type AnalyticsReview = {
  status: string
  text: string
}


export type ReleaseAcceptanceCheck = {
  name: string
  status: string
  message: string
}

export type ReleaseReport = {
  generated_at: string
  project: string
  version: string
  environment: string
  preflight: PreflightStatus
  readiness: ReleaseReadiness
  codex: CodexStatus
  deepseek: DeepSeekStatus
  state: SystemState
  acceptance_checks: ReleaseAcceptanceCheck[]
  overall_status: string
  recommended_mode: string
  journal_entries: number
  bot_runs: number
  system_events: number
  backup_artifacts: BackupArtifact[]
  release_artifacts: BackupArtifact[]
  next_actions: string[]
}

export type ReleaseAcceptanceRun = {
  generated_at: string
  overall_status: string
  recommended_mode: string
  score: number
  ready_for_paper: boolean
  ready_for_live: boolean
  json_artifact: BackupArtifact
  markdown_artifact: BackupArtifact
  critical_issues: string[]
  warnings: string[]
  next_actions: string[]
}
