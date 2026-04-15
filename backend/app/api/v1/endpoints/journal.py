from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import db_session
from app.models.journal import JournalEntry
from app.schemas.journal import JournalEntryRead, JournalSummaryRead
from app.services.ai_review import AIReviewService
from app.services.trading import TradingService

router = APIRouter()


@router.get('/entries', response_model=list[JournalEntryRead])
def list_entries(db: Session = Depends(db_session)) -> list[JournalEntryRead]:
    return [JournalEntryRead.model_validate(item, from_attributes=True) for item in TradingService(db).journal_entries()]


@router.get('/summary', response_model=JournalSummaryRead)
def summary(db: Session = Depends(db_session)) -> JournalSummaryRead:
    return JournalSummaryRead(**TradingService(db).journal_summary())


@router.post('/entries/{entry_id}/review', response_model=JournalEntryRead)
async def generate_review(entry_id: int, db: Session = Depends(db_session)) -> JournalEntryRead:
    entry = db.get(JournalEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail='Journal entry not found')
    status, text = await AIReviewService().review_journal_entry(entry)
    entry.ai_review_status = status
    entry.ai_review_text = text
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return JournalEntryRead.model_validate(entry, from_attributes=True)


@router.post('/review/pending', response_model=list[JournalEntryRead])
async def review_pending(limit: int = Query(default=5, ge=1, le=50), db: Session = Depends(db_session)) -> list[JournalEntryRead]:
    entries = [item for item in TradingService(db).journal_entries() if item.ai_review_status in {'pending', 'fallback', 'error'}][:limit]
    service = AIReviewService()
    for entry in entries:
        status, text = await service.review_journal_entry(entry)
        entry.ai_review_status = status
        entry.ai_review_text = text
        db.add(entry)
    db.commit()
    refreshed: list[JournalEntryRead] = []
    for entry in entries:
        db.refresh(entry)
        refreshed.append(JournalEntryRead.model_validate(entry, from_attributes=True))
    return refreshed
