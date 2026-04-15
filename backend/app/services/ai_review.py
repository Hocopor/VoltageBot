from __future__ import annotations

from app.models.journal import JournalEntry
from app.models.strategy import StrategyDecision
from app.services.deepseek import DeepSeekClient


class AIReviewService:
    def __init__(self) -> None:
        self.client = DeepSeekClient()

    async def review_journal_entry(self, entry: JournalEntry) -> tuple[str, str]:
        prompt = (
            'Ты анализируешь завершённую крипто-сделку торговой системы VOLTAGE. '
            'Сделай короткий разбор: соблюдение стратегии, качество входа, управление риском, итоги и выводы. '
            f'Сделка: symbol={entry.symbol}, mode={entry.mode}, market={entry.market_type}, direction={entry.direction}, '
            f'entry={entry.entry_price}, exit={entry.exit_price}, stop={entry.stop_loss}, tp1={entry.take_profit_1}, '
            f'tp2={entry.take_profit_2}, tp3={entry.take_profit_3}, pnl={entry.realized_pnl}, close_reason={entry.close_reason}, '
            f'hold_minutes={entry.hold_minutes}, best_price={entry.best_price}, worst_price={entry.worst_price}, '
            f'mfe_pnl={entry.mfe_pnl}, mae_pnl={entry.mae_pnl}, scenario={entry.strategy_scenario}, '
            f'compliance_score={entry.compliance_score}, tags={entry.tags}. Не выдумывай данных, которых нет.'
        )
        payload = await self.client.chat(
            [
                {'role': 'system', 'content': 'Ты торговый аналитик для дневника трейдера.'},
                {'role': 'user', 'content': prompt},
            ]
        )
        choices = payload.get('choices') if isinstance(payload, dict) else None
        if choices:
            content = choices[0].get('message', {}).get('content', '').strip()
            if content:
                return 'completed', content
        fallback = self._fallback_review(entry)
        status = 'fallback' if isinstance(payload, dict) and payload.get('status') == 'disabled' else 'completed'
        return status, fallback

    async def explain_strategy_decision(self, decision: StrategyDecision) -> tuple[str, str]:
        prompt = (
            'Объясни решение стратегии VOLTAGE простым и инженерно-полезным языком. '
            f'symbol={decision.symbol}, allowed={decision.allowed}, scenario={decision.market_scenario}, '
            f'confidence={decision.confidence}, filters={decision.filter_summary}, risk={decision.risk_summary}. '
            'Нужно коротко: что увидела стратегия, почему вход разрешён или заблокирован, на что обратить внимание оператору.'
        )
        payload = await self.client.chat(
            [
                {'role': 'system', 'content': 'Ты explainability-слой торговой платформы VOLTAGE.'},
                {'role': 'user', 'content': prompt},
            ]
        )
        choices = payload.get('choices') if isinstance(payload, dict) else None
        if choices:
            content = choices[0].get('message', {}).get('content', '').strip()
            if content:
                return 'completed', content
        fallback = self._fallback_decision_explanation(decision)
        status = 'fallback' if isinstance(payload, dict) and payload.get('status') == 'disabled' else 'completed'
        return status, fallback

    async def summarize_analytics(self, overview: dict) -> tuple[str, str]:
        prompt = (
            'Сделай короткий итог по торговой аналитике VOLTAGE. '
            f"total_trades={overview.get('total_trades')}, realized_pnl={overview.get('realized_pnl')}, "
            f"profit_factor={overview.get('profit_factor')}, average_rr={overview.get('average_rr')}, "
            f"max_drawdown={overview.get('max_drawdown')}, by_mode={overview.get('by_mode')}, "
            f"by_market={overview.get('by_market')}, by_symbol={overview.get('by_symbol')}, "
            f"by_direction={overview.get('by_direction')}, by_close_reason={overview.get('by_close_reason')}, "
            f"streaks={overview.get('streaks')}, average_compliance_score={overview.get('average_compliance_score')}. "
            'Ответ в 4 коротких пунктах: сильные стороны, слабые стороны, риск, следующий фокус анализа.'
        )
        payload = await self.client.chat(
            [
                {'role': 'system', 'content': 'Ты аналитик торговой статистики.'},
                {'role': 'user', 'content': prompt},
            ]
        )
        choices = payload.get('choices') if isinstance(payload, dict) else None
        if choices:
            content = choices[0].get('message', {}).get('content', '').strip()
            if content:
                return 'completed', content
        fallback = self._fallback_analytics_summary(overview)
        status = 'fallback' if isinstance(payload, dict) and payload.get('status') == 'disabled' else 'completed'
        return status, fallback

    def _fallback_review(self, entry: JournalEntry) -> str:
        pnl_state = 'прибыльная' if entry.realized_pnl > 0 else 'убыточная' if entry.realized_pnl < 0 else 'нейтральная'
        rr_hint = ''
        if entry.stop_loss and entry.exit_price:
            risk = abs(entry.entry_price - entry.stop_loss)
            reward = abs(entry.exit_price - entry.entry_price)
            if risk > 0:
                rr_hint = f' Приблизительный R/R по фактическому выходу: {reward / risk:.2f}.'
        compliance_hint = ''
        if entry.compliance_score is not None:
            compliance_hint = f' Оценка соблюдения стратегии: {entry.compliance_score:.2f}.'
        close_hint = f' Причина закрытия: {entry.close_reason}.' if entry.close_reason else ''
        return (
            f'Сделка {pnl_state}. Режим: {entry.mode}, рынок: {entry.market_type}, инструмент: {entry.symbol}.{close_hint}'
            ' Проверьте, был ли вход выполнен только после прохождения всех 6 фильтров VOLTAGE, '
            'и соответствовал ли стоп размещению за зоной ликвидности.'
            f'{rr_hint}{compliance_hint} Основной вывод: соблюдать обязательную структуру TP1/TP2/TP3 и избегать ручных отклонений от стратегии.'
        )

    def _fallback_decision_explanation(self, decision: StrategyDecision) -> str:
        verdict = 'разрешён' if decision.allowed else 'заблокирован'
        return (
            f'Сигнал по {decision.symbol} {verdict}. Сценарий рынка: {decision.market_scenario or "не определён"}. '
            f'Уверенность: {decision.confidence:.2f}. '
            f'Фильтры: {decision.filter_summary or "нет сводки"}. '
            f'Риск: {decision.risk_summary or "нет сводки"}. '
            'Оператору важно проверить, что вход соответствует VOLTAGE без ручных отклонений.'
        )

    def _fallback_analytics_summary(self, overview: dict) -> str:
        return (
            f"Сильная сторона: profit factor {overview.get('profit_factor', 0):.2f}, average R/R {overview.get('average_rr', 0):.2f}. "
            f"Слабая сторона: drawdown {overview.get('max_drawdown', 0):.2f}% и распределение по причинам закрытия {overview.get('by_close_reason', {})}. "
            f"Риск: концентрация результатов по инструментам {overview.get('by_symbol', {})} и режимам {overview.get('by_mode', {})}. "
            f"Следующий фокус: проверить дисциплину стратегии, средний compliance score {overview.get('average_compliance_score', 0):.2f}."
        )
