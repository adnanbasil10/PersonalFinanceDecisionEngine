"""
Explain routes: reasoning for recommendations and model insights.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routes.auth import get_current_user
from app.schemas.prediction import (
    ExplainResponse, Explanation, FeatureImpact, ModelMetrics,
)
from app.services.transaction_service import TransactionService
from app.services.decision_engine import DecisionEngine
from app.services.explainability import ExplainabilityEngine

router = APIRouter(prefix="/explain", tags=["Explainability"])


@router.get("", response_model=ExplainResponse)
def get_explanations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get detailed explanations for each recommendation.
    Includes feature importance, reasoning text, and contributing factors.
    """
    df = TransactionService.get_all_as_dataframe(db, current_user.id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No transactions found.")

    # Load models
    from app.ml.classifier import SpendingClassifier
    from app.ml.risk_predictor import OverspendRiskPredictor
    from app.ml.forecaster import SpendingForecaster

    try:
        classifier = SpendingClassifier.load()
        risk_predictor = OverspendRiskPredictor.load()
        forecaster = SpendingForecaster.load()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="ML models not trained yet.")

    # Get predictions
    risk_prediction = risk_predictor.predict(df, current_user.monthly_income)
    forecast_result = forecaster.predict(df, days=30)

    # Generate recommendations
    engine = DecisionEngine(monthly_income=current_user.monthly_income)
    rec_result = engine.generate_recommendations(
        transactions_df=df,
        risk_prediction=risk_prediction,
        forecast_result=forecast_result,
    )

    # Generate explanations
    explainer = ExplainabilityEngine(monthly_income=current_user.monthly_income)
    explainer.set_feature_importances(
        classifier_importance=classifier.get_feature_importance(),
        risk_importance=risk_predictor.get_feature_importance(),
    )

    raw_explanations = explainer.explain_recommendations(
        recommendations=rec_result["recommendations"],
        transactions_df=df,
        risk_prediction=risk_prediction,
        forecast_result=forecast_result,
    )

    # Format explanations
    explanations = [
        Explanation(
            recommendation_index=exp["recommendation_index"],
            reasoning=exp["reasoning"],
            feature_impacts=[
                FeatureImpact(**fi) for fi in exp.get("feature_impacts", [])
            ],
            contributing_factors=exp.get("contributing_factors", []),
        )
        for exp in raw_explanations
    ]

    # Load model metrics
    metrics = explainer.load_metrics()

    return ExplainResponse(
        explanations=explanations,
        model_metrics={k: v for k, v in metrics.items() if isinstance(v, (int, float))},
        feature_importance_global=explainer.get_global_feature_importance(),
    )


@router.get("/metrics", response_model=ModelMetrics)
def get_model_metrics(current_user: User = Depends(get_current_user)):
    """Get ML model evaluation metrics."""
    explainer = ExplainabilityEngine(monthly_income=current_user.monthly_income)
    metrics = explainer.load_metrics()

    if not metrics:
        raise HTTPException(status_code=503, detail="No metrics found. Train models first.")

    return ModelMetrics(
        classifier_accuracy=metrics.get("classifier_accuracy", 0),
        classifier_f1=metrics.get("classifier_f1_macro", 0),
        risk_auc_roc=metrics.get("risk_auc_roc", 0),
        risk_f1=metrics.get("risk_f1", 0),
        forecast_rmse=metrics.get("forecast_rmse"),
        forecast_mape=metrics.get("forecast_mape"),
    )
