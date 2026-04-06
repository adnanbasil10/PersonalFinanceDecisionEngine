"""
Feature engineering and preprocessing pipeline.
Transforms raw transactions into ML-ready features.
"""

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib
import os


SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


class TransactionFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom transformer that creates time-based and spending-based features
    from raw transaction data.
    """

    def __init__(self):
        self.merchant_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        self._is_fitted = False

    def fit(self, X: pd.DataFrame, y=None):
        df = X.copy()
        if "merchant" in df.columns:
            df["merchant"] = df["merchant"].fillna("Unknown")
            self.merchant_encoder.fit(df["merchant"])
        if "category" in df.columns:
            self.category_encoder.fit(df["category"])
        self._is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        df = X.copy()

        # Parse dates
        df["date"] = pd.to_datetime(df["date"])

        # Time features
        df["day_of_week"] = df["date"].dt.dayofweek
        df["day_of_month"] = df["date"].dt.day
        df["month"] = df["date"].dt.month
        df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
        df["is_month_start"] = (df["day_of_month"] <= 5).astype(int)
        df["is_month_end"] = (df["day_of_month"] >= 25).astype(int)
        df["quarter"] = df["date"].dt.quarter
        df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)

        # Amount features
        df["log_amount"] = np.log1p(df["amount"])
        df["amount_squared"] = df["amount"] ** 2

        # Merchant encoding
        if "merchant" in df.columns:
            df["merchant"] = df["merchant"].fillna("Unknown")
            # Handle unseen merchants
            known_merchants = set(self.merchant_encoder.classes_)
            df["merchant_clean"] = df["merchant"].apply(
                lambda x: x if x in known_merchants else "Unknown"
            )
            if "Unknown" not in self.merchant_encoder.classes_:
                self.merchant_encoder.classes_ = np.append(self.merchant_encoder.classes_, "Unknown")
            df["merchant_encoded"] = self.merchant_encoder.transform(df["merchant_clean"])
            df = df.drop(columns=["merchant_clean"])

        return df


def build_classifier_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Build feature matrix for spending classification.
    Returns feature DataFrame and list of feature column names.
    """
    feature_cols = [
        "day_of_week", "day_of_month", "month", "is_weekend",
        "is_month_start", "is_month_end", "quarter", "week_of_year",
        "log_amount", "amount", "merchant_encoded",
    ]
    available_cols = [c for c in feature_cols if c in df.columns]
    return df[available_cols], available_cols


def build_risk_features(
    df: pd.DataFrame, monthly_income: float
) -> pd.DataFrame:
    """
    Build monthly aggregate features for overspend risk prediction.
    Each row = one month for one user.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["year_month"] = df["date"].dt.to_period("M")

    monthly = df.groupby("year_month").agg(
        total_spending=("amount", "sum"),
        transaction_count=("amount", "count"),
        avg_transaction=("amount", "mean"),
        max_transaction=("amount", "max"),
        std_transaction=("amount", "std"),
        unique_categories=("category", "nunique"),
        unique_merchants=("merchant", "nunique"),
    ).reset_index()

    # Category spending ratios
    category_monthly = df.groupby(["year_month", "category"])["amount"].sum().unstack(fill_value=0)
    category_ratios = category_monthly.div(category_monthly.sum(axis=1), axis=0)
    category_ratios.columns = [f"ratio_{c.lower().replace(' ', '_')}" for c in category_ratios.columns]
    category_ratios = category_ratios.reset_index()

    monthly = monthly.merge(category_ratios, on="year_month", how="left")

    # Income-based features
    monthly["spending_to_income"] = monthly["total_spending"] / monthly_income
    monthly["is_overspend"] = (monthly["total_spending"] > monthly_income * 0.9).astype(int)

    # Rolling features (lag-based)
    monthly = monthly.sort_values("year_month")
    monthly["prev_month_spending"] = monthly["total_spending"].shift(1)
    monthly["spending_change"] = monthly["total_spending"].pct_change()
    monthly["rolling_3m_avg"] = monthly["total_spending"].rolling(3, min_periods=1).mean()
    monthly["rolling_3m_std"] = monthly["total_spending"].rolling(3, min_periods=1).std().fillna(0)

    monthly = monthly.dropna(subset=["prev_month_spending"])

    return monthly


def build_forecast_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build daily aggregate data for time-series forecasting.
    Returns DataFrame with columns: ds, y (Prophet format).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    daily = df.groupby("date")["amount"].sum().reset_index()
    daily.columns = ["ds", "y"]
    daily = daily.sort_values("ds")
    return daily


def save_preprocessor(feature_engineer: TransactionFeatureEngineer):
    """Save the fitted preprocessor to disk."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    path = os.path.join(SAVE_DIR, "preprocessor.joblib")
    joblib.dump(feature_engineer, path)
    print(f"Preprocessor saved to {path}")


def load_preprocessor() -> TransactionFeatureEngineer:
    """Load the fitted preprocessor from disk."""
    path = os.path.join(SAVE_DIR, "preprocessor.joblib")
    return joblib.load(path)
