"""
Pydantic schemas for ML predictions, recommendations, and explanations.
"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date


# --- Prediction Schemas ---

class CategoryPrediction(BaseModel):
    transaction_id: int
    predicted_category: str
    confidence: float


class RiskPrediction(BaseModel):
    overspend_probability: float
    risk_level: str  # "low", "medium", "high", "critical"
    days_remaining: int
    current_spending: float
    projected_spending: float
    monthly_income: float


class ForecastPoint(BaseModel):
    date: date
    predicted_amount: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    forecast: List[ForecastPoint]
    total_predicted: float
    forecast_days: int
    model_used: str  # "prophet" or "regression_fallback"
    rmse: Optional[float] = None
    mape: Optional[float] = None


class PredictionResponse(BaseModel):
    category_predictions: List[CategoryPrediction]
    risk: RiskPrediction
    forecast: ForecastResponse


# --- Recommendation Schemas ---

class Recommendation(BaseModel):
    type: str  # "warning", "suggestion", "alert"
    priority: str  # "high", "medium", "low"
    message: str
    confidence: float
    category: Optional[str] = None
    amount: Optional[float] = None


class RecommendationResponse(BaseModel):
    recommendations: List[Recommendation]
    generated_at: str
    summary: str


# --- Explanation Schemas ---

class FeatureImpact(BaseModel):
    feature: str
    importance: float
    direction: str  # "positive", "negative"
    description: str


class Explanation(BaseModel):
    recommendation_index: int
    reasoning: str
    feature_impacts: List[FeatureImpact]
    contributing_factors: List[str]


from pydantic import ConfigDict

class ExplainResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    explanations: List[Explanation]
    model_metrics: Dict[str, float]
    feature_importance_global: Dict[str, float]


# --- Metrics ---

class ModelMetrics(BaseModel):
    classifier_accuracy: float
    classifier_f1: float
    risk_auc_roc: float
    risk_f1: float
    forecast_rmse: Optional[float] = None
    forecast_mape: Optional[float] = None
