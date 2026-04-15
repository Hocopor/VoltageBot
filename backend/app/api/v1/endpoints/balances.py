from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models.account import RuntimeSetting
from app.schemas.balance import BalanceItem, BalanceOverview
from app.services.balance_service import BalanceService

router = APIRouter()


@router.get('/overview', response_model=BalanceOverview)
async def get_balance_overview(db: Session = Depends(db_session)) -> BalanceOverview:
    settings = db.query(RuntimeSetting).order_by(RuntimeSetting.id.asc()).first()
    runtime_mode = settings.mode if settings else 'paper'
    spot_working = settings.spot_working_balance if settings else 0.0
    futures_working = settings.futures_working_balance if settings else 0.0

    balances = await BalanceService(db).overview()
    total_wallet_usd = round(sum(item.usd_value for item in balances), 2)

    return BalanceOverview(
        mode=runtime_mode,
        total_wallet_usd=total_wallet_usd,
        spot_working_balance=spot_working,
        futures_working_balance=futures_working,
        balances=[
            BalanceItem(
                asset=item.asset,
                total=item.total,
                available=item.available,
                usd_value=item.usd_value,
                market_type=item.market_type,
            )
            for item in balances
        ],
    )
