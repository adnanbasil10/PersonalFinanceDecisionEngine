"""
Overspending Risk Predictor using XGBoost.
Binary classification: Will the user overspend this month? (Yes/No)
Outputs probability score (0.0 - 1.0).
"""

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score, precision_score, recall_score,
    classification_report,
)
import joblib
import os

from app.ml.preprocessor import build_risk_features


SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")

# Risk thresholds
RISK_THRESHOLDS = {
    "low": 0.3,
    "medium": 0.5,
    "high": 0.7,
    "critical": 0.85,
}

class DummyModel:
    def __init__(self, pred, n_features):
        self.pred = pred
        self.classes_ = np.array([0, 1])
        self.feature_importances_ = np.zeros(n_features)
    def fit(self, X, y):
        pass
    def predict(self, X):
        return np.full(len(X), self.pred)
    def predict_proba(self, X):
        prob = np.zeros((len(X), 2))
        prob[:, self.pred] = 1.0
        return prob



class OverspendRiskPredictor:
    """
    XGBoost binary classifier for predicting monthly overspending risk.
    """

    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=150,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            scale_pos_weight=2.0,  # Handle class imbalance
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            use_label_encoder=False,
            eval_metric="logloss",
            n_jobs=-1,
        )
        self.feature_columns = []
        self.metrics = {}

    def train(self, df: pd.DataFrame, monthly_income: float) -> dict:
        """
        Train the risk predictor on transaction data.

        Args:
            df: Raw transaction DataFrame
            monthly_income: User's monthly income

        Returns:
            Dictionary of evaluation metrics
        """
        print("\n" + "=" * 60)
        print("TRAINING: Overspend Risk Predictor (XGBoost)")
        print("=" * 60)

        # Build monthly features
        monthly = build_risk_features(df, monthly_income)

        # Define feature columns (exclude target and non-feature cols)
        exclude_cols = {"year_month", "is_overspend"}
        self.feature_columns = [c for c in monthly.columns if c not in exclude_cols]

        X = monthly[self.feature_columns].fillna(0)
        y = monthly["is_overspend"].values

        # Handle case where there is only one class
        if len(np.unique(y)) < 2:
            print("Only one class present in target variable. Creating a constant predictor.")
            majority_class = y[0] if len(y) > 0 else 0
            
            self.model = DummyModel(majority_class, len(self.feature_columns))
            self.metrics = {
                "risk_accuracy": 1.0,
                "risk_f1": 0.0,
                "risk_precision": 0.0,
                "risk_recall": 0.0,
                "risk_auc_roc": 0.5,
                "n_months": len(X),
                "overspend_rate": round(float(y.mean()) if len(y) > 0 else 0.0, 4),
            }
            return self.metrics

        # Cross-validation (use fewer folds if few samples)
        n_splits = min(5, max(2, len(X) // 3))
        
        # Check if we have enough samples for the minority class
        class_counts = np.bincount(y) if len(y) > 0 else []
        min_class_count = np.min(class_counts) if len(class_counts) > 1 else 0

        if len(X) >= 6 and min_class_count >= n_splits:
            skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
            y_pred_cv = cross_val_predict(self.model, X, y, cv=skf)
            y_prob_cv = cross_val_predict(self.model, X, y, cv=skf, method="predict_proba")[:, 1]

            cv_accuracy = accuracy_score(y, y_pred_cv)
            cv_f1 = f1_score(y, y_pred_cv, zero_division=0)
            cv_precision = precision_score(y, y_pred_cv, zero_division=0)
            cv_recall = recall_score(y, y_pred_cv, zero_division=0)

            try:
                cv_auc = roc_auc_score(y, y_prob_cv)
            except ValueError:
                cv_auc = 0.5

            print(f"\nCross-Validation Results ({n_splits}-Fold):")
            print(f"  Accuracy:  {cv_accuracy:.4f}")
            print(f"  F1:        {cv_f1:.4f}")
            print(f"  Precision: {cv_precision:.4f}")
            print(f"  Recall:    {cv_recall:.4f}")
            print(f"  AUC-ROC:   {cv_auc:.4f}")
        elif len(X) >= 4 and min_class_count >= 1:
            # Fallback to train/test split
            print("\nNot enough samples for K-Fold CV, using train_test_split.")
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
            self.model.fit(X_train, y_train)
            y_pred = self.model.predict(X_test)
            y_prob = self.model.predict_proba(X_test)[:, 1]
            
            cv_accuracy = accuracy_score(y_test, y_pred)
            cv_f1 = f1_score(y_test, y_pred, zero_division=0)
            cv_precision = precision_score(y_test, y_pred, zero_division=0)
            cv_recall = recall_score(y_test, y_pred, zero_division=0)
            
            try:
                cv_auc = roc_auc_score(y_test, y_prob)
            except ValueError:
                cv_auc = 0.5
                
            print(f"  Accuracy:  {cv_accuracy:.4f}")
            print(f"  F1:        {cv_f1:.4f}")
            print(f"  Precision: {cv_precision:.4f}")
            print(f"  Recall:    {cv_recall:.4f}")
            print(f"  AUC-ROC:   {cv_auc:.4f}")
        else:
            cv_accuracy = cv_f1 = cv_precision = cv_recall = cv_auc = 0.0
            print("Too few samples for cross-validation, training directly.")

        # Train final model
        self.model.fit(X, y)

        self.metrics = {
            "risk_accuracy": round(cv_accuracy, 4),
            "risk_f1": round(cv_f1, 4),
            "risk_precision": round(cv_precision, 4),
            "risk_recall": round(cv_recall, 4),
            "risk_auc_roc": round(cv_auc, 4),
            "n_months": len(X),
            "overspend_rate": round(float(y.mean()), 4),
        }

        return self.metrics

    def predict(self, df: pd.DataFrame, monthly_income: float) -> dict:
        """
        Predict overspend risk for the current/latest month.

        Returns:
            Dict with probability, risk level, and spending projections.
        """
        monthly = build_risk_features(df, monthly_income)

        if monthly.empty:
            return {
                "overspend_probability": 0.0,
                "risk_level": "low",
                "current_spending": 0.0,
                "projected_spending": 0.0,
            }

        # Use the latest month
        latest = monthly.iloc[[-1]]
        X = latest[self.feature_columns].fillna(0)

        probability = float(self.model.predict_proba(X)[0][1])

        # Determine risk level
        risk_level = "low"
        for level, threshold in sorted(RISK_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if probability >= threshold:
                risk_level = level
                break

        return {
            "overspend_probability": round(probability, 4),
            "risk_level": risk_level,
            "current_spending": round(float(latest["total_spending"].values[0]), 2),
            "projected_spending": round(
                float(latest["total_spending"].values[0]) * (30 / max(1, 15)), 2
            ),
            "monthly_income": monthly_income,
        }

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance scores."""
        importances = self.model.feature_importances_
        return {
            col: round(float(imp), 4)
            for col, imp in sorted(
                zip(self.feature_columns, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        }

    def save(self):
        """Save the trained model."""
        os.makedirs(SAVE_DIR, exist_ok=True)
        joblib.dump(self.model, os.path.join(SAVE_DIR, "risk_model.joblib"))
        joblib.dump(self.feature_columns, os.path.join(SAVE_DIR, "risk_features.joblib"))
        print(f"Risk predictor saved to {SAVE_DIR}")

    @classmethod
    def load(cls) -> "OverspendRiskPredictor":
        """Load a trained risk predictor."""
        instance = cls()
        instance.model = joblib.load(os.path.join(SAVE_DIR, "risk_model.joblib"))
        instance.feature_columns = joblib.load(os.path.join(SAVE_DIR, "risk_features.joblib"))
        return instance
