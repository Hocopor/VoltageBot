from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.schemas.analytics import AnalyticsOverviewRead, AnalyticsReviewRead
from app.services.ai_review import AIReviewService
from app.services.trading import TradingService

router = APIRouter()


@router.get('/overview', response_model=AnalyticsOverviewRead)
def analytics_overview(db: Session = Depends(db_session)) -> AnalyticsOverviewRead:
    return AnalyticsOverviewRead(**TradingService(db).analytics_overview())


@router.post('/summary/review', response_model=AnalyticsReviewRead)
async def analytics_review(db: Session = Depends(db_session)) -> AnalyticsReviewRead:
    overview = TradingService(db).analytics_overview()
    status, text = await AIReviewService().summarize_analytics(overview)
    return AnalyticsReviewRead(status=status, text=text)
