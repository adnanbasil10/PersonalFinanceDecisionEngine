"""
Transaction service layer.
Handles business logic for transaction CRUD and aggregation.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date, datetime
from typing import Optional

from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionSummary


class TransactionService:
    """Service for managing user transactions."""

    @staticmethod
    def create_transaction(db: Session, user_id: int, data: TransactionCreate) -> Transaction:
        """Create a single transaction."""
        txn = Transaction(
            user_id=user_id,
            date=data.date,
            amount=data.amount,
            category=data.category.value,
            merchant=data.merchant,
            description=data.description,
        )
        db.add(txn)
        db.commit()
        db.refresh(txn)
        return txn

    @staticmethod
    def bulk_create(db: Session, user_id: int, transactions: list[TransactionCreate]) -> list[Transaction]:
        """Create multiple transactions in bulk."""
        txns = []
        for data in transactions:
            txn = Transaction(
                user_id=user_id,
                date=data.date,
                amount=data.amount,
                category=data.category.value,
                merchant=data.merchant,
                description=data.description,
            )
            txns.append(txn)
        db.add_all(txns)
        db.commit()
        for txn in txns:
            db.refresh(txn)
        return txns

    @staticmethod
    def get_transactions(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[Transaction]:
        """Get user transactions with optional filters."""
        query = db.query(Transaction).filter(Transaction.user_id == user_id)

        if category:
            query = query.filter(Transaction.category == category)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        return query.order_by(Transaction.date.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_summary(
        db: Session,
        user_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> TransactionSummary:
        """Get spending summary for a given month."""
        now = datetime.now()
        year = year or now.year
        month = month or now.month

        query = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            extract("year", Transaction.date) == year,
            extract("month", Transaction.date) == month,
        )

        transactions = query.all()

        if not transactions:
            return TransactionSummary(
                total_spending=0.0,
                transaction_count=0,
                category_breakdown={},
                daily_average=0.0,
                top_merchants=[],
                month=f"{year}-{month:02d}",
            )

        total = sum(t.amount for t in transactions)
        count = len(transactions)

        # Category breakdown
        cat_totals = {}
        for t in transactions:
            cat_totals[t.category] = cat_totals.get(t.category, 0) + t.amount

        # Top merchants
        merchant_totals = {}
        for t in transactions:
            if t.merchant:
                merchant_totals[t.merchant] = merchant_totals.get(t.merchant, 0) + t.amount

        top_merchants = sorted(
            [{"merchant": m, "amount": round(a, 2)} for m, a in merchant_totals.items()],
            key=lambda x: x["amount"],
            reverse=True,
        )[:10]

        # Daily average
        unique_days = len(set(t.date for t in transactions))
        daily_avg = total / max(1, unique_days)

        return TransactionSummary(
            total_spending=round(total, 2),
            transaction_count=count,
            category_breakdown={k: round(v, 2) for k, v in cat_totals.items()},
            daily_average=round(daily_avg, 2),
            top_merchants=top_merchants,
            month=f"{year}-{month:02d}",
        )

    @staticmethod
    def get_all_as_dataframe(db: Session, user_id: int):
        """Get all user transactions as a pandas DataFrame for ML."""
        import pandas as pd

        transactions = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.date)
            .all()
        )

        if not transactions:
            return pd.DataFrame(columns=["date", "amount", "category", "merchant", "description"])

        return pd.DataFrame([
            {
                "date": t.date.isoformat(),
                "amount": t.amount,
                "category": t.category,
                "merchant": t.merchant or "Unknown",
                "description": t.description or "",
            }
            for t in transactions
        ])
