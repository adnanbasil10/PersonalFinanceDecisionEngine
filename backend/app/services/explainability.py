"""
Explainability Layer.
Provides feature importance, natural language reasoning,
and per-recommendation explanations.
"""

import json
import os
from typing import Optional

import numpy as np
import pandas as pd
from datetime import datetime


class ExplainabilityEngine:
    """
    Generates human-readable explanations for ML predictions and recommendations.
    Uses feature importance + rule-based reasoning templates.
    """

    def __init__(self, monthly_income: float):
        self.monthly_income = monthly_income
        self.classifier_importance = {}
        self.risk_importance = {}

    def set_feature_importances(
        self,
        classifier_importance: dict = None,
        risk_importance: dict = None,
    ):
        """Set feature importances from trained models."""
        if classifier_importance:
            self.classifier_importance = classifier_importance
        if risk_importance:
            self.risk_importance = risk_importance

    def explain_recommendations(
        self,
        recommendations: list,
        transactions_df: pd.DataFrame,
        risk_prediction: dict,
        forecast_result: dict,
    ) -> list:
        """
        Generate detailed explanations for each recommendation.

        Returns:
            List of explanation dicts with reasoning, feature impacts, and contributing factors.
        """
        explanations = []

        for idx, rec in enumerate(recommendations):
            explanation = {
                "recommendation_index": idx,
                "reasoning": "",
                "feature_impacts": [],
                "contributing_factors": [],
            }

            rec_type = rec.get("type", "")
            category = rec.get("category")
            message = rec.get("message", "")

            # Generate reasoning based on recommendation type
            if "overspend" in message.lower() or "risk" in message.lower():
                explanation = self._explain_risk(
                    explanation, risk_prediction, transactions_df
                )
            elif category and category in self._get_category_stats(transactions_df):
                explanation = self._explain_category_spending(
                    explanation, category, transactions_df
                )
            elif "forecast" in message.lower():
                explanation = self._explain_forecast(
                    explanation, forecast_result, transactions_df
                )
            elif "invest" in message.lower() or "saving" in message.lower():
                explanation = self._explain_savings(
                    explanation, transactions_df
                )
            elif "unusual" in message.lower() or "anomal" in message.lower():
                explanation = self._explain_anomaly(
                    explanation, category, transactions_df
                )
            elif "trend" in message.lower() or "increas" in message.lower():
                explanation = self._explain_trend(explanation, transactions_df)
            else:
                explanation["reasoning"] = (
                    "This recommendation is based on your overall spending patterns "
                    "and financial health indicators."
                )
                explanation["contributing_factors"] = [
                    "Overall spending analysis",
                    "Income-to-expense ratio",
                ]

            explanations.append(explanation)

        return explanations

    def _explain_risk(
        self, explanation: dict, risk_prediction: dict, df: pd.DataFrame
    ) -> dict:
        """Explain overspend risk prediction."""
        prob = risk_prediction.get("overspend_probability", 0)
        current = risk_prediction.get("current_spending", 0)
        projected = risk_prediction.get("projected_spending", 0)

        factors = []
        impacts = []

        # Spending velocity
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        recent_30 = df[df["date"] >= (datetime.now() - pd.Timedelta(days=30))]
        recent_7 = df[df["date"] >= (datetime.now() - pd.Timedelta(days=7))]

        if not recent_30.empty and not recent_7.empty:
            monthly_rate = recent_30["amount"].sum()
            weekly_rate = recent_7["amount"].sum() * 4.3
            if weekly_rate > monthly_rate * 1.2:
                factors.append("Spending velocity is accelerating — recent week is above monthly average")

        # Top risk features from model
        for feature, importance in list(self.risk_importance.items())[:5]:
            impacts.append({
                "feature": feature.replace("_", " ").title(),
                "importance": round(importance, 4),
                "direction": "positive" if importance > 0 else "negative",
                "description": self._describe_feature(feature),
            })

        factors.extend([
            f"Current spending is {current / self.monthly_income:.0%} of monthly income",
            f"Model predicts {prob:.0%} probability of exceeding budget",
        ])

        explanation["reasoning"] = (
            f"The overspend risk score of {prob:.0%} is driven by your current spending "
            f"trajectory (₹{current:,.0f} so far this month) relative to your income of "
            f"₹{self.monthly_income:,.0f}. "
            f"{'Spending velocity has increased recently, ' if len(factors) > 2 else ''}"
            f"contributing to the elevated risk assessment."
        )
        explanation["feature_impacts"] = impacts
        explanation["contributing_factors"] = factors

        return explanation

    def _explain_category_spending(
        self, explanation: dict, category: str, df: pd.DataFrame
    ) -> dict:
        """Explain category-specific overspending."""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        stats = self._get_category_stats(df)
        cat_stats = stats.get(category, {})

        current_pct = cat_stats.get("pct_of_income", 0)
        trend = cat_stats.get("trend", "stable")
        monthly_avg = cat_stats.get("monthly_avg", 0)

        from app.services.decision_engine import CATEGORY_THRESHOLDS
        threshold = CATEGORY_THRESHOLDS.get(category, 0.15)

        explanation["reasoning"] = (
            f"Your {category.lower()} spending is {current_pct:.0%} of income "
            f"(recommended threshold: {threshold:.0%}). "
            f"Average monthly spend: ₹{monthly_avg:,.0f}. "
            f"{'The trend is increasing, amplifying the concern.' if trend == 'increasing' else ''} "
            f"Reducing by ₹{max(0, monthly_avg - self.monthly_income * threshold):,.0f}/month "
            f"would bring it within recommended limits."
        )

        explanation["feature_impacts"] = [
            {
                "feature": f"{category} Spending %",
                "importance": round(current_pct, 4),
                "direction": "positive",
                "description": f"Percentage of income spent on {category.lower()}",
            },
            {
                "feature": f"{category} Trend",
                "importance": 0.3 if trend == "increasing" else 0.1,
                "direction": "positive" if trend == "increasing" else "negative",
                "description": f"Spending trend for {category.lower()} is {trend}",
            },
        ]

        explanation["contributing_factors"] = [
            f"High {category.lower()} spending at {current_pct:.0%} of income",
            f"{'Increasing' if trend == 'increasing' else 'Stable'} spending trend",
            f"Monthly average: ₹{monthly_avg:,.0f}",
        ]

        return explanation

    def _explain_forecast(
        self, explanation: dict, forecast_result: dict, df: pd.DataFrame
    ) -> dict:
        """Explain forecast-based recommendation."""
        total = forecast_result.get("total_predicted", 0)
        days = forecast_result.get("forecast_days", 30)
        model = forecast_result.get("model_used", "unknown")

        explanation["reasoning"] = (
            f"Based on {model} forecasting model analysis of your historical spending, "
            f"the projected spending of ₹{total:,.0f} over {days} days suggests "
            f"{'budget pressure' if total > self.monthly_income * 0.8 else 'manageable spending'}. "
            f"This forecast accounts for weekly patterns, seasonal trends, and your recent behavior."
        )

        explanation["feature_impacts"] = [
            {
                "feature": "Historical Spending Pattern",
                "importance": 0.4,
                "direction": "positive",
                "description": "Past spending behavior is the strongest predictor",
            },
            {
                "feature": "Weekly Seasonality",
                "importance": 0.25,
                "direction": "positive",
                "description": "Day-of-week spending patterns affect projections",
            },
        ]

        explanation["contributing_factors"] = [
            f"Forecast model: {model}",
            f"Projected {days}-day total: ₹{total:,.0f}",
            f"RMSE: {forecast_result.get('rmse', 'N/A')}",
        ]

        return explanation

    def _explain_savings(self, explanation: dict, df: pd.DataFrame) -> dict:
        """Explain savings/investment recommendation."""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        total_spending = df["amount"].sum()
        months = max(1, df["date"].dt.to_period("M").nunique())
        monthly_avg = total_spending / months
        savings = self.monthly_income - monthly_avg
        savings_rate = savings / self.monthly_income

        explanation["reasoning"] = (
            f"Your average monthly spending of ₹{monthly_avg:,.0f} leaves "
            f"₹{savings:,.0f} in savings ({savings_rate:.0%} savings rate). "
            f"Financial advisors recommend investing surplus beyond 20% of income "
            f"for long-term wealth building. SIPs in diversified equity funds "
            f"or debt funds are good starting options."
        )

        explanation["contributing_factors"] = [
            f"Savings rate: {savings_rate:.0%}",
            f"Monthly surplus: ₹{savings:,.0f}",
            f"Consistent positive cash flow observed",
        ]

        return explanation

    def _explain_anomaly(
        self, explanation: dict, category: str, df: pd.DataFrame
    ) -> dict:
        """Explain anomaly detection."""
        explanation["reasoning"] = (
            f"This transaction was flagged because it significantly deviates "
            f"from your typical spending in the {category or 'this'} category. "
            f"Transactions exceeding 3 standard deviations from the mean "
            f"are considered unusual and may warrant review."
        )

        explanation["contributing_factors"] = [
            "Amount significantly exceeds category average",
            "Statistical outlier (>3 standard deviations)",
            "May indicate an error or one-time expense",
        ]

        return explanation

    def _explain_trend(self, explanation: dict, df: pd.DataFrame) -> dict:
        """Explain trend-based recommendation."""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()

        if len(monthly) >= 3:
            recent = monthly.tail(3).values
            change = (recent[-1] - recent[0]) / recent[0] * 100

            explanation["reasoning"] = (
                f"Your spending has increased by {change:.0f}% over the last 3 months "
                f"(₹{recent[0]:,.0f} → ₹{recent[-1]:,.0f}). "
                f"If this trend continues, you risk exceeding your budget. "
                f"Identifying and reducing discretionary expenses can help stabilize spending."
            )

            explanation["contributing_factors"] = [
                f"3-month spending increase: {change:.0f}%",
                f"Month 1: ₹{recent[0]:,.0f}",
                f"Month 3: ₹{recent[-1]:,.0f}",
            ]

        return explanation

    def _get_category_stats(self, df: pd.DataFrame) -> dict:
        """Calculate per-category statistics."""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        stats = {}
        months = max(1, df["date"].dt.to_period("M").nunique())

        for category in df["category"].unique():
            cat_data = df[df["category"] == category]
            monthly_avg = cat_data["amount"].sum() / months
            pct = monthly_avg / self.monthly_income

            # Trend detection
            monthly_series = cat_data.groupby(cat_data["date"].dt.to_period("M"))["amount"].sum()
            if len(monthly_series) >= 3:
                recent = monthly_series.tail(3).values
                trend = "increasing" if recent[-1] > recent[0] * 1.1 else "stable"
            else:
                trend = "stable"

            stats[category] = {
                "monthly_avg": round(monthly_avg, 2),
                "pct_of_income": round(pct, 4),
                "trend": trend,
                "total": round(cat_data["amount"].sum(), 2),
            }

        return stats

    def _describe_feature(self, feature_name: str) -> str:
        """Get human-friendly description for a feature name."""
        descriptions = {
            "total_spending": "Total amount spent in the period",
            "transaction_count": "Number of transactions made",
            "avg_transaction": "Average transaction amount",
            "max_transaction": "Largest single transaction",
            "spending_to_income": "Ratio of spending to monthly income",
            "prev_month_spending": "Previous month's total spending",
            "spending_change": "Month-over-month spending change",
            "rolling_3m_avg": "3-month rolling average of spending",
            "rolling_3m_std": "Spending volatility over 3 months",
            "unique_categories": "Number of spending categories used",
            "unique_merchants": "Number of unique merchants",
        }
        return descriptions.get(feature_name, f"Model feature: {feature_name}")

    def get_global_feature_importance(self) -> dict:
        """Return combined global feature importance from all models."""
        combined = {}
        for feat, imp in self.classifier_importance.items():
            combined[f"classifier_{feat}"] = imp
        for feat, imp in self.risk_importance.items():
            combined[f"risk_{feat}"] = imp
        # Sort by importance
        return dict(sorted(combined.items(), key=lambda x: x[1], reverse=True)[:20])

    def load_metrics(self) -> dict:
        """Load saved model metrics from disk."""
        metrics_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "ml", "saved_models", "metrics.json",
        )
        if os.path.exists(metrics_path):
            with open(metrics_path) as f:
                return json.load(f)
        return {}
