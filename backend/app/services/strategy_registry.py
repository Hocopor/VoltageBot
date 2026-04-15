from __future__ import annotations

from pathlib import Path


class StrategyRegistry:
    def get_voltage(self) -> dict[str, str | bool]:
        strategy_path = Path(__file__).resolve().parent.parent / 'strategy' / 'voltage.md'
        return {
            'name': 'VOLTAGE',
            'version': '1.0.0',
            'immutable': True,
            'text': strategy_path.read_text(encoding='utf-8').strip(),
        }
