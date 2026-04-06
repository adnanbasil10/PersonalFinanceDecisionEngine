"""
Prediction routes: spending classification, risk prediction, forecasting.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.prediction import (
    PredictionResponse, CategoryPrediction,
    RiskPrediction, ForecastResponse, ForecastPoint,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/predict", tags=["Predictions"])


def _get_models():
    """Load ML models (lazy load)."""
    from app.ml.classifier import SpendingClassifier
    from app.ml.risk_predictor import OverspendRiskPredictor
    from app.ml.forecaster import SpendingForecaster
    from app.ml.preprocessor import load_preprocessor

    try:
        classifier = SpendingClassifier.load()
        risk_predictor = OverspendRiskPredictor.load()
        forecaster = SpendingForecaster.load()
        preprocessor = load_preprocessor()
        return classifier, risk_predictor, forecaster, preprocessor
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="ML models not trained yet. Run 'python -m app.ml.train' first.",
        )


@router.get("", response_model=PredictionResponse)
def get_predictions(
    forecast_days: int = Query(30, ge=10, le=60),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all ML predictions:
    - Category classification for transactions
    - Overspend risk probability
    - Spending forecast
    """
    # Load user data
    df = TransactionService.get_all_as_dataframe(db, current_user.id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No transactions found. Upload data first.")

    classifier, risk_predictor, forecaster, preprocessor = _get_models()

    # 1. Category predictions
    predictions = classifier.predict(df, preprocessor)
    category_preds = [
        CategoryPrediction(
            transaction_id=i + 1,
            predicted_category=p["predicted_category"],
            confidence=p["confidence"],
        )
        for i, p in enumerate(predictions[-10:])  # Last 10 transactions
    ]

    # 2. Risk prediction
    risk_result = risk_predictor.predict(df, current_user.monthly_income)
    risk = RiskPrediction(
        overspend_probability=risk_result["overspend_probability"],
        risk_level=risk_result["risk_level"],
        days_remaining=30,  # Days remaining in month
        current_spending=risk_result["current_spending"],
        projected_spending=risk_result["projected_spending"],
        monthly_income=current_user.monthly_income,
    )

    # 3. Forecast
    forecast_result = forecaster.predict(df, days=forecast_days)
    forecast = ForecastResponse(
        forecast=[
            ForecastPoint(
                date=p["date"],
                predicted_amount=p["predicted_amount"],
                lower_bound=p["lower_bound"],
                upper_bound=p["upper_bound"],
            )
            for p in forecast_result["forecast"]
        ],
        total_predicted=forecast_result["total_predicted"],
        forecast_days=forecast_result["forecast_days"],
        model_used=forecast_result["model_used"],
        rmse=forecast_result.get("rmse"),
        mape=forecast_result.get("mape"),
    )

    return PredictionResponse(
        category_predictions=category_preds,
        risk=risk,
        forecast=forecast,
    )
