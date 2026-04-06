"""
Time-Series Spending Forecaster.
Primary: Facebook Prophet
Fallback: Rolling regression with scikit-learn
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
import joblib
import json
import os
import warnings

from app.ml.preprocessor import build_forecast_data

warnings.filterwarnings("ignore", category=FutureWarning)

SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


class SpendingForecaster:
    """
    Time-series forecaster for daily spending prediction.
    Uses Prophet as primary model with Ridge regression fallback.
    """

    def __init__(self):
        self.model = None
        self.model_type = None  # "prophet" or "regression_fallback"
        self.metrics = {}
        self.fallback_model = None
        self.fallback_scaler = None

    def train(self, df: pd.DataFrame, forecast_days: int = 30) -> dict:
        """
        Train the forecaster on historical transaction data.

        Args:
            df: Raw transaction DataFrame
            forecast_days: Number of days to forecast

        Returns:
            Dictionary of evaluation metrics
        """
        print("\n" + "=" * 60)
        print("TRAINING: Spending Forecaster")
        print("=" * 60)

        daily = build_forecast_data(df)
        print(f"Daily data points: {len(daily)}")
        print(f"Date range: {daily['ds'].min()} to {daily['ds'].max()}")

        # Try Prophet first
        try:
            metrics = self._train_prophet(daily, forecast_days)
            self.model_type = "prophet"
            print(f"\nUsing Prophet model")
        except Exception as e:
            print(f"\nProphet failed: {e}")
            print("Falling back to Ridge regression...")
            metrics = self._train_regression(daily, forecast_days)
            self.model_type = "regression_fallback"

        self.metrics = metrics
        return metrics

    def _train_prophet(self, daily: pd.DataFrame, forecast_days: int) -> dict:
        """Train with Facebook Prophet."""
        from prophet import Prophet

        # Train/test split (last 30 days for validation)
        split_idx = max(len(daily) - forecast_days, int(len(daily) * 0.8))
        train = daily.iloc[:split_idx]
        test = daily.iloc[split_idx:]

        # Configure Prophet
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True if len(daily) > 365 else False,
            changepoint_prior_scale=0.05,
            seasonality_prior_scale=10.0,
        )

        # Add monthly seasonality
        model.add_seasonality(name="monthly", period=30.5, fourier_order=5)

        # Suppress verbose output
        model.fit(train)

        # Evaluate on test set
        if len(test) > 0:
            future_test = model.make_future_dataframe(periods=len(test))
            forecast_full = model.predict(future_test)
            forecast_test = forecast_full.iloc[split_idx:]

            y_true = test["y"].values
            y_pred = forecast_test["yhat"].values[:len(y_true)]

            rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
            mape = float(mean_absolute_percentage_error(y_true, y_pred)) * 100
        else:
            rmse = mape = 0.0

        self.model = model

        metrics = {
            "forecast_rmse": round(rmse, 2),
            "forecast_mape": round(mape, 2),
            "model_type": "prophet",
            "training_days": len(train),
            "test_days": len(test),
        }

        print(f"  RMSE:  {rmse:.2f}")
        print(f"  MAPE:  {mape:.2f}%")

        return metrics

    def _train_regression(self, daily: pd.DataFrame, forecast_days: int) -> dict:
        """Train with Ridge regression on rolling features (fallback)."""
        df = daily.copy()
        df = df.sort_values("ds").reset_index(drop=True)

        # Create rolling features
        for window in [3, 7, 14, 30]:
            df[f"rolling_mean_{window}"] = df["y"].rolling(window, min_periods=1).mean()
            df[f"rolling_std_{window}"] = df["y"].rolling(window, min_periods=1).std().fillna(0)

        # Add time features
        df["day_of_week"] = pd.to_datetime(df["ds"]).dt.dayofweek
        df["day_of_month"] = pd.to_datetime(df["ds"]).dt.day
        df["month"] = pd.to_datetime(df["ds"]).dt.month

        # Lag features
        for lag in [1, 2, 3, 7]:
            df[f"lag_{lag}"] = df["y"].shift(lag)

        df = df.dropna()

        feature_cols = [c for c in df.columns if c not in ["ds", "y"]]

        # Train/test split
        split_idx = max(len(df) - forecast_days, int(len(df) * 0.8))
        train = df.iloc[:split_idx]
        test = df.iloc[split_idx:]

        X_train = train[feature_cols]
        y_train = train["y"]
        X_test = test[feature_cols]
        y_test = test["y"]

        model = Ridge(alpha=1.0)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
        mape = float(mean_absolute_percentage_error(y_test, y_pred)) * 100

        self.fallback_model = model
        self.fallback_features = feature_cols
        self.fallback_daily = df

        metrics = {
            "forecast_rmse": round(rmse, 2),
            "forecast_mape": round(mape, 2),
            "model_type": "regression_fallback",
            "training_days": len(train),
            "test_days": len(test),
        }

        print(f"  RMSE:  {rmse:.2f}")
        print(f"  MAPE:  {mape:.2f}%")

        return metrics

    def predict(self, df: pd.DataFrame, days: int = 30) -> dict:
        """
        Generate spending forecast for the next N days.

        Args:
            df: Raw transaction DataFrame (for context)
            days: Number of days to forecast

        Returns:
            Dict with forecast points, totals, and model info
        """
        if self.model_type == "prophet":
            return self._predict_prophet(days)
        else:
            return self._predict_regression(df, days)

    def _predict_prophet(self, days: int) -> dict:
        """Generate forecast using Prophet."""
        future = self.model.make_future_dataframe(periods=days)
        forecast = self.model.predict(future)

        # Get only future dates
        forecast_future = forecast.tail(days)

        points = []
        for _, row in forecast_future.iterrows():
            points.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "predicted_amount": round(max(0, float(row["yhat"])), 2),
                "lower_bound": round(max(0, float(row["yhat_lower"])), 2),
                "upper_bound": round(max(0, float(row["yhat_upper"])), 2),
            })

        total = sum(p["predicted_amount"] for p in points)

        return {
            "forecast": points,
            "total_predicted": round(total, 2),
            "forecast_days": days,
            "model_used": "prophet",
            "rmse": self.metrics.get("forecast_rmse"),
            "mape": self.metrics.get("forecast_mape"),
        }

    def _predict_regression(self, df: pd.DataFrame, days: int) -> dict:
        """Generate forecast using regression fallback."""
        daily = build_forecast_data(df)
        daily = daily.sort_values("ds").reset_index(drop=True)

        # Build rolling features for latest data
        for window in [3, 7, 14, 30]:
            daily[f"rolling_mean_{window}"] = daily["y"].rolling(window, min_periods=1).mean()
            daily[f"rolling_std_{window}"] = daily["y"].rolling(window, min_periods=1).std().fillna(0)

        daily["day_of_week"] = pd.to_datetime(daily["ds"]).dt.dayofweek
        daily["day_of_month"] = pd.to_datetime(daily["ds"]).dt.day
        daily["month"] = pd.to_datetime(daily["ds"]).dt.month

        for lag in [1, 2, 3, 7]:
            daily[f"lag_{lag}"] = daily["y"].shift(lag)

        daily = daily.dropna()

        if len(daily) == 0:
            # Fallback if the user has < 7 days of transacting history
            points = []
            last_date = pd.to_datetime(df["date"].max()) if not df.empty else pd.to_datetime('today')
            for i in range(days):
                next_date = last_date + pd.Timedelta(days=i + 1)
                points.append({
                    "date": next_date.strftime("%Y-%m-%d"),
                    "predicted_amount": 0.0,
                    "lower_bound": 0.0,
                    "upper_bound": 0.0,
                })
            return {
                "forecast": points,
                "total_predicted": 0.0,
                "forecast_days": days,
                "model_used": "Insufficient Data",
                "rmse": 0.0,
                "mape": 0.0,
            }

        # Predict iteratively
        points = []
        last_row = daily.iloc[-1].copy()
        last_date = pd.to_datetime(daily["ds"].iloc[-1])

        for i in range(days):
            next_date = last_date + pd.Timedelta(days=i + 1)
            feature_row = last_row[self.fallback_features].values.reshape(1, -1)
            pred = max(0, float(self.fallback_model.predict(feature_row)[0]))

            points.append({
                "date": next_date.strftime("%Y-%m-%d"),
                "predicted_amount": round(pred, 2),
                "lower_bound": round(pred * 0.7, 2),
                "upper_bound": round(pred * 1.3, 2),
            })

        total = sum(p["predicted_amount"] for p in points)

        return {
            "forecast": points,
            "total_predicted": round(total, 2),
            "forecast_days": days,
            "model_used": "regression_fallback",
            "rmse": self.metrics.get("forecast_rmse"),
            "mape": self.metrics.get("forecast_mape"),
        }

    def save(self):
        """Save the trained forecaster."""
        os.makedirs(SAVE_DIR, exist_ok=True)

        if self.model_type == "prophet":
            # Prophet serialization via JSON
            from prophet.serialize import model_to_json
            with open(os.path.join(SAVE_DIR, "forecaster.json"), "w") as f:
                f.write(model_to_json(self.model))
        else:
            joblib.dump(self.fallback_model, os.path.join(SAVE_DIR, "forecaster_regression.joblib"))
            joblib.dump(self.fallback_features, os.path.join(SAVE_DIR, "forecaster_features.joblib"))

        # Save metadata
        meta = {"model_type": self.model_type, "metrics": self.metrics}
        with open(os.path.join(SAVE_DIR, "forecaster_meta.json"), "w") as f:
            json.dump(meta, f, indent=2)

        print(f"Forecaster ({self.model_type}) saved to {SAVE_DIR}")

    @classmethod
    def load(cls) -> "SpendingForecaster":
        """Load a trained forecaster."""
        instance = cls()

        meta_path = os.path.join(SAVE_DIR, "forecaster_meta.json")
        with open(meta_path) as f:
            meta = json.load(f)

        instance.model_type = meta["model_type"]
        instance.metrics = meta["metrics"]

        if instance.model_type == "prophet":
            from prophet.serialize import model_from_json
            with open(os.path.join(SAVE_DIR, "forecaster.json")) as f:
                instance.model = model_from_json(f.read())
        else:
            instance.fallback_model = joblib.load(os.path.join(SAVE_DIR, "forecaster_regression.joblib"))
            instance.fallback_features = joblib.load(os.path.join(SAVE_DIR, "forecaster_features.joblib"))

        return instance
