"""
Recommendation routes: actionable financial decisions.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.prediction import RecommendationResponse, Recommendation
from app.services.transaction_service import TransactionService
from app.services.decision_engine import DecisionEngine

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.get("", response_model=RecommendationResponse)
def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get actionable financial recommendations.
    Combines ML predictions with financial rules.
    """
    # Load user data
    df = TransactionService.get_all_as_dataframe(db, current_user.id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No transactions found. Upload data first.")

    # Load ML models (Graceful fallback if missing)
    from app.ml.risk_predictor import OverspendRiskPredictor
    from app.ml.forecaster import SpendingForecaster

    risk_prediction = {"overspend_probability": 0, "risk_level": "unknown"}
    forecast_result = {"total_predicted": 0, "forecast_days": 30}

    try:
        risk_predictor = OverspendRiskPredictor.load()
        forecaster = SpendingForecaster.load()
        
        # Get ML predictions
        risk_prediction = risk_predictor.predict(df, current_user.monthly_income)
        forecast_result = forecaster.predict(df, days=30)
    except Exception as e:
        print(f"Decision Engine warning: Running in heuristic-only mode (Models missing: {e})")


    # Run decision engine
    engine = DecisionEngine(monthly_income=current_user.monthly_income)
    result = engine.generate_recommendations(
        transactions_df=df,
        risk_prediction=risk_prediction,
        forecast_result=forecast_result,
    )

    return RecommendationResponse(
        recommendations=[
            Recommendation(**rec) for rec in result["recommendations"]
        ],
        generated_at=result["generated_at"],
        summary=result["summary"],
    )
