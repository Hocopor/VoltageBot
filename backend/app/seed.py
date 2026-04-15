from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.account import RuntimeSetting
from app.models.system import BotConfig, SystemState


def seed_runtime_state() -> None:
    with SessionLocal() as db:
        runtime = db.scalar(select(RuntimeSetting).limit(1))
        if runtime is None:
            db.add(
                RuntimeSetting(
                    mode='paper',
                    spot_enabled=True,
                    futures_enabled=False,
                    paper_start_balance=10000.0,
                    history_start_balance=10000.0,
                    spot_working_balance=1000.0,
                    futures_working_balance=1000.0,
                    notes='Initial seeded runtime settings',
                )
            )
            db.commit()

        bot_cfg = db.scalar(select(BotConfig).limit(1))
        if bot_cfg is None:
            db.add(
                BotConfig(
                    enabled=False,
                    auto_execute=True,
                    live_execution_allowed=False,
                    scan_interval_seconds=300,
                    strategy_timeframe='1H',
                    strategy_candles=240,
                    risk_percent=0.01,
                    max_new_positions_per_cycle=2,
                    notes='Initial seeded bot config',
                )
            )
            db.commit()

        system_state = db.scalar(select(SystemState).limit(1))
        if system_state is None:
            db.add(
                SystemState(
                    maintenance_mode=False,
                    trading_paused=False,
                    kill_switch_armed=False,
                    boot_count=0,
                    last_live_sync_status='never',
                    last_live_sync_message='System state initialized',
                )
            )
            db.commit()
