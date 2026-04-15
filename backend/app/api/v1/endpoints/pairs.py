from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models.market import PairSelection
from app.schemas.market import PairSelectionsRead, PairSelectionsUpdate, SymbolItem
from app.services.bybit import BybitPublicService

router = APIRouter()


@router.get('/spot', response_model=list[SymbolItem])
async def get_spot_pairs() -> list[SymbolItem]:
    return [SymbolItem(symbol=s, market_type='spot') for s in await BybitPublicService().fetch_symbols('spot')]


@router.get('/futures', response_model=list[SymbolItem])
async def get_futures_pairs() -> list[SymbolItem]:
    return [SymbolItem(symbol=s, market_type='futures') for s in await BybitPublicService().fetch_symbols('linear')]


@router.get('/selections', response_model=PairSelectionsRead)
def get_pair_selections(db: Session = Depends(db_session)) -> PairSelectionsRead:
    spot_symbols = [x.symbol for x in db.scalars(select(PairSelection).where(PairSelection.market_type == 'spot', PairSelection.selected.is_(True))).all()]
    futures_symbols = [x.symbol for x in db.scalars(select(PairSelection).where(PairSelection.market_type == 'futures', PairSelection.selected.is_(True))).all()]
    return PairSelectionsRead(spot_symbols=spot_symbols, futures_symbols=futures_symbols)


@router.post('/selections', response_model=PairSelectionsRead)
def save_pair_selections(payload: PairSelectionsUpdate, db: Session = Depends(db_session)) -> PairSelectionsRead:
    db.execute(delete(PairSelection).where(PairSelection.market_type.in_(['spot', 'futures'])))
    for symbol in payload.spot_symbols:
        db.add(PairSelection(market_type='spot', symbol=symbol, selected=True))
    for symbol in payload.futures_symbols:
        db.add(PairSelection(market_type='futures', symbol=symbol, selected=True))
    db.commit()
    return PairSelectionsRead(spot_symbols=payload.spot_symbols, futures_symbols=payload.futures_symbols)
