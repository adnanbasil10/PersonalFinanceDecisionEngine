"""
Pydantic schemas for Transaction endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class SpendingCategory(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    ENTERTAINMENT = "Entertainment"
    SHOPPING = "Shopping"
    BILLS = "Bills"
    HEALTHCARE = "Healthcare"
    EDUCATION = "Education"
    GROCERIES = "Groceries"
    RENT = "Rent"
    UTILITIES = "Utilities"
    SUBSCRIPTIONS = "Subscriptions"
    TRAVEL = "Travel"
    PERSONAL_CARE = "Personal Care"
    GIFTS = "Gifts"
    INVESTMENTS = "Investments"
    OTHER = "Other"


class TransactionCreate(BaseModel):
    date: date
    amount: float = Field(..., gt=0, description="Transaction amount (positive)")
    category: SpendingCategory
    merchant: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("date")
    @classmethod
    def date_not_future(cls, v):
        if v > date.today():
            raise ValueError("Transaction date cannot be in the future")
        return v


class TransactionBulkUpload(BaseModel):
    transactions: List[TransactionCreate] = Field(..., min_length=1, max_length=1000)


class TransactionOut(BaseModel):
    id: int
    user_id: int
    date: date
    amount: float
    category: str
    merchant: Optional[str]
    description: Optional[str]
    predicted_category: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionSummary(BaseModel):
    total_spending: float
    transaction_count: int
    category_breakdown: dict[str, float]
    daily_average: float
    top_merchants: list[dict]
    month: str
