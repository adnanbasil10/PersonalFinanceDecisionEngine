"""
Transaction routes: upload, list, summary.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.transaction import (
    TransactionCreate, TransactionBulkUpload,
    TransactionOut, TransactionSummary,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a single transaction."""
    txn = TransactionService.create_transaction(db, current_user.id, data)
    return TransactionOut.model_validate(txn)


@router.post("/bulk", response_model=list[TransactionOut], status_code=201)
def bulk_upload(
    data: TransactionBulkUpload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload multiple transactions at once (max 1000)."""
    txns = TransactionService.bulk_create(db, current_user.id, data.transactions)
    return [TransactionOut.model_validate(t) for t in txns]


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user transactions with optional filters."""
    txns = TransactionService.get_transactions(
        db, current_user.id, skip, limit, category, start_date, end_date
    )
    return [TransactionOut.model_validate(t) for t in txns]


@router.get("/summary", response_model=TransactionSummary)
def get_summary(
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get spending summary for a given month."""
    return TransactionService.get_summary(db, current_user.id, year, month)
