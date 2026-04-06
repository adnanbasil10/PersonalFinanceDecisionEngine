"""
Decision Engine.
Combines ML model outputs with financial rules to generate
actionable, prioritized recommendations.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


# Category spending thresholds (percentage of income)
CATEGORY_THRESHOLDS = {
    "Food": 0.30,
    "Shopping": 0.15,
    "Entertainment": 0.10,
    "Transport": 0.15,
    "Travel": 0.10,
    "Subscriptions": 0.05,
    "Personal Care": 0.05,
    "Gifts": 0.05,
}

# Savings/investment thresholds
SAVINGS_INVEST_THRESHOLD = 0.20  # If savings > 20% income → suggest investment
MIN_EMERGENCY_FUND_MONTHS = 3


class DecisionEngine:
    """
    Hybrid decision engine: ML predictions + financial rules → recommendations.
    """

    def __init__(self, monthly_income: float):
        self.monthly_income = monthly_income

    def generate_recommendations(
        self,
        transactions_df: pd.DataFrame,
        risk_prediction: dict,
        forecast_result: dict,
        category_predictions: list = None,
    ) -> dict:
        """
        Generate a full set of recommendations from ML outputs + rules.

        Args:
            transactions_df: User's transaction data
            risk_prediction: Output from OverspendRiskPredictor.predict()
            forecast_result: Output from SpendingForecaster.predict()
            category_predictions: Output from SpendingClassifier.predict()

        Returns:
            Dict with recommendations list and summary
        """
        recommendations = []

        # Rule 1: Category overspending detection
        recommendations.extend(
            self._check_category_overspending(transactions_df)
        )

        # Rule 2: Overspend risk warnings
        recommendations.extend(
            self._check_risk_warnings(risk_prediction)
        )

        # Rule 3: Forecast-based alerts
        recommendations.extend(
            self._check_forecast_alerts(forecast_result)
        )

        # Rule 4: Savings & investment suggestions
        recommendations.extend(
            self._check_savings_opportunities(transactions_df)
        )

        # Rule 5: Spending anomaly detection
        recommendations.extend(
            self._detect_anomalies(transactions_df)
        )

        # Rule 6: Spending trend analysis
        recommendations.extend(
            self._analyze_trends(transactions_df)
        )

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 99))

        # Generate summary
        high_count = sum(1 for r in recommendations if r["priority"] == "high")
        summary = self._generate_summary(recommendations, high_count)

        return {
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "summary": summary,
        }

    def _check_category_overspending(self, df: pd.DataFrame) -> list:
        """Check if any category exceeds its spending threshold."""
        recs = []
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # Current month spending
        now = datetime.now()
        current_month = df[
            (df["date"].dt.year == now.year) & (df["date"].dt.month == now.month)
        ]

        if current_month.empty:
            # Use latest month with data
            latest_month = df["date"].dt.to_period("M").max()
            current_month = df[df["date"].dt.to_period("M") == latest_month]

        if current_month.empty:
            return recs

        total_spending = current_month["amount"].sum()
        category_spending = current_month.groupby("category")["amount"].sum()

        for category, threshold in CATEGORY_THRESHOLDS.items():
            if category in category_spending.index:
                spent = category_spending[category]
                pct = spent / self.monthly_income
                threshold_amount = self.monthly_income * threshold

                if pct > threshold:
                    excess = spent - threshold_amount
                    excess_pct = ((pct - threshold) / threshold) * 100

                    priority = "high" if pct > threshold * 1.5 else "medium"

                    recs.append({
                        "type": "warning",
                        "priority": priority,
                        "message": (
                            f"Reduce {category.lower()} spending by ₹{excess:,.0f} "
                            f"({pct:.0%} of income vs {threshold:.0%} recommended threshold)"
                        ),
                        "confidence": min(0.95, 0.7 + (pct - threshold)),
                        "category": category,
                        "amount": round(excess, 2),
                    })

        return recs

    def _check_risk_warnings(self, risk_prediction: dict) -> list:
        """Generate warnings based on overspend risk probability."""
        recs = []
        prob = risk_prediction.get("overspend_probability", 0)
        risk_level = risk_prediction.get("risk_level", "low")

        if prob > 0.7:
            recs.append({
                "type": "alert",
                "priority": "high",
                "message": (
                    f"⚠️ High risk of overspending this month! "
                    f"Probability: {prob:.0%}. "
                    f"Projected spending: ₹{risk_prediction.get('projected_spending', 0):,.0f} "
                    f"vs income ₹{self.monthly_income:,.0f}"
                ),
                "confidence": prob,
                "category": None,
                "amount": None,
            })
        elif prob > 0.5:
            recs.append({
                "type": "warning",
                "priority": "medium",
                "message": (
                    f"Moderate overspending risk detected ({prob:.0%} probability). "
                    f"Consider reducing discretionary spending."
                ),
                "confidence": prob,
                "category": None,
                "amount": None,
            })
        elif prob > 0.3:
            recs.append({
                "type": "suggestion",
                "priority": "low",
                "message": (
                    f"Slight overspending risk ({prob:.0%} probability). "
                    f"You're mostly on track — keep monitoring."
                ),
                "confidence": prob,
                "category": None,
                "amount": None,
            })

        return recs

    def _check_forecast_alerts(self, forecast_result: dict) -> list:
        """Generate alerts based on spending forecast."""
        recs = []
        total_predicted = forecast_result.get("total_predicted", 0)
        days = forecast_result.get("forecast_days", 30)

        # Projected monthly equivalent
        monthly_projected = (total_predicted / max(1, days)) * 30

        if monthly_projected > self.monthly_income * 0.95:
            recs.append({
                "type": "alert",
                "priority": "high",
                "message": (
                    f"Forecast shows spending of ₹{total_predicted:,.0f} over next {days} days. "
                    f"This exceeds your income — immediate action recommended!"
                ),
                "confidence": 0.85,
                "category": None,
                "amount": round(monthly_projected - self.monthly_income, 2),
            })
        elif monthly_projected > self.monthly_income * 0.8:
            recs.append({
                "type": "warning",
                "priority": "medium",
                "message": (
                    f"Forecast predicts ₹{total_predicted:,.0f} spending in {days} days "
                    f"({monthly_projected / self.monthly_income:.0%} of income). Monitor closely."
                ),
                "confidence": 0.75,
                "category": None,
                "amount": None,
            })

        return recs

    def _check_savings_opportunities(self, df: pd.DataFrame) -> list:
        """Suggest investment opportunities based on savings rate."""
        recs = []
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        # Average monthly spending over last 3 months
        recent = df[df["date"] >= (datetime.now() - timedelta(days=90))]
        if recent.empty:
            recent = df

        monthly_avg = recent["amount"].sum() / max(1, recent["date"].dt.to_period("M").nunique())
        savings = self.monthly_income - monthly_avg
        savings_rate = savings / self.monthly_income

        if savings_rate > SAVINGS_INVEST_THRESHOLD:
            investable = savings * 0.5  # Suggest investing 50% of savings
            recs.append({
                "type": "suggestion",
                "priority": "low",
                "message": (
                    f"💰 You can safely invest ₹{investable:,.0f}/month! "
                    f"Your savings rate is {savings_rate:.0%} "
                    f"(₹{savings:,.0f}/month surplus). "
                    f"Consider SIPs in index funds or fixed deposits."
                ),
                "confidence": 0.8,
                "category": "Investments",
                "amount": round(investable, 2),
            })

        if savings > 0 and savings_rate > 0.1:
            emergency_fund = self.monthly_income * MIN_EMERGENCY_FUND_MONTHS
            recs.append({
                "type": "suggestion",
                "priority": "low",
                "message": (
                    f"Maintain an emergency fund of at least ₹{emergency_fund:,.0f} "
                    f"({MIN_EMERGENCY_FUND_MONTHS} months expenses)."
                ),
                "confidence": 0.7,
                "category": None,
                "amount": round(emergency_fund, 2),
            })

        return recs

    def _detect_anomalies(self, df: pd.DataFrame) -> list:
        """Detect unusual spending patterns."""
        recs = []
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])

        for category in df["category"].unique():
            cat_data = df[df["category"] == category]["amount"]
            if len(cat_data) < 5:
                continue

            mean_val = cat_data.mean()
            std_val = cat_data.std()

            if std_val == 0:
                continue

            # Find transactions > 3 standard deviations
            anomalies = df[
                (df["category"] == category) &
                (df["amount"] > mean_val + 3 * std_val)
            ]

            for _, row in anomalies.iterrows():
                recs.append({
                    "type": "alert",
                    "priority": "medium",
                    "message": (
                        f"Unusual {category.lower()} transaction of ₹{row['amount']:,.0f} "
                        f"detected on {row['date'].strftime('%Y-%m-%d')} "
                        f"(category average: ₹{mean_val:,.0f})"
                    ),
                    "confidence": 0.85,
                    "category": category,
                    "amount": round(row["amount"], 2),
                })

        return recs[:5]  # Limit to top 5 anomalies

    def _analyze_trends(self, df: pd.DataFrame) -> list:
        """Analyze spending trends for alerts."""
        recs = []
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["year_month"] = df["date"].dt.to_period("M")

        monthly = df.groupby("year_month")["amount"].sum()
        if len(monthly) < 3:
            return recs

        # Check if spending is consistently increasing
        recent_3 = monthly.tail(3).values
        if len(recent_3) == 3 and all(recent_3[i] < recent_3[i + 1] for i in range(2)):
            increase_pct = (recent_3[-1] - recent_3[0]) / recent_3[0] * 100
            recs.append({
                "type": "warning",
                "priority": "medium",
                "message": (
                    f"📈 Spending has increased {increase_pct:.0f}% over the last 3 months. "
                    f"Review and adjust your budget to prevent overspending."
                ),
                "confidence": 0.75,
                "category": None,
                "amount": None,
            })

        return recs

    def _generate_summary(self, recommendations: list, high_count: int) -> str:
        """Generate a human-readable summary of all recommendations."""
        total = len(recommendations)
        if total == 0:
            return "Your finances look healthy! No immediate actions needed."

        if high_count >= 3:
            return (
                f"⚠️ {high_count} critical issues found. "
                f"Immediate attention required on spending and budget management."
            )
        elif high_count >= 1:
            return (
                f"{total} recommendations generated, including {high_count} high-priority alert(s). "
                f"Review the critical items first."
            )
        else:
            return (
                f"{total} suggestions to optimize your finances. "
                f"No critical issues — focus on long-term improvements."
            )
