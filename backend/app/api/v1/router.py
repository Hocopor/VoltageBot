from fastapi import APIRouter

from app.api.v1.endpoints import analytics, auth, backtest, balances, bot, journal, operations, pairs, settings, strategy, trading

api_router = APIRouter()
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(settings.router, prefix='/settings', tags=['settings'])
api_router.include_router(pairs.router, prefix='/pairs', tags=['pairs'])
api_router.include_router(balances.router, prefix='/balances', tags=['balances'])
api_router.include_router(strategy.router, prefix='/strategy', tags=['strategy'])
api_router.include_router(trading.router, prefix='/trade', tags=['trade'])
api_router.include_router(backtest.router, prefix='/backtest', tags=['backtest'])
api_router.include_router(journal.router, prefix='/journal', tags=['journal'])
api_router.include_router(analytics.router, prefix='/analytics', tags=['analytics'])
api_router.include_router(bot.router, prefix='/bot', tags=['bot'])
api_router.include_router(operations.router, prefix='/ops', tags=['ops'])
