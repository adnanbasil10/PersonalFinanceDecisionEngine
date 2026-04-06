"""
Spending Category Classifier using XGBoost.
Classifies transactions into spending categories based on
amount, timing, and merchant features.
"""

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import (
    accuracy_score, f1_score, classification_report, confusion_matrix
)
from sklearn.preprocessing import LabelEncoder
import joblib
import os
import json

from app.ml.preprocessor import (
    TransactionFeatureEngineer,
    build_classifier_features,
)


SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


class SpendingClassifier:
    """
    XGBoost-based spending category classifier.
    Predicts transaction category from features like amount, time, and merchant.
    """

    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            random_state=42,
            use_label_encoder=False,
            eval_metric="mlogloss",
            n_jobs=-1,
        )
        self.label_encoder = LabelEncoder()
        self.feature_columns = []
        self.metrics = {}

    def train(self, df: pd.DataFrame, feature_engineer: TransactionFeatureEngineer):
        """
        Train the classifier on preprocessed transaction data.

        Args:
            df: DataFrame with raw transaction data
            feature_engineer: Fitted TransactionFeatureEngineer
        """
        print("\n" + "=" * 60)
        print("TRAINING: Spending Category Classifier (XGBoost)")
        print("=" * 60)

        # Preprocess
        processed = feature_engineer.transform(df)

        # Build features
        X, self.feature_columns = build_classifier_features(processed)
        y = self.label_encoder.fit_transform(df["category"])

        print(f"Features: {self.feature_columns}")
        print(f"Classes: {list(self.label_encoder.classes_)}")
        print(f"Training samples: {len(X)}")

        # Stratified K-Fold cross-validation
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        y_pred_cv = cross_val_predict(self.model, X, y, cv=skf)

        # Compute CV metrics
        cv_accuracy = accuracy_score(y, y_pred_cv)
        cv_f1 = f1_score(y, y_pred_cv, average="macro")

        print(f"\nCross-Validation Results (5-Fold):")
        print(f"  Accuracy:  {cv_accuracy:.4f}")
        print(f"  F1 (macro): {cv_f1:.4f}")
        print(f"\nClassification Report:")
        print(classification_report(
            y, y_pred_cv,
            target_names=self.label_encoder.classes_,
        ))

        # Train final model on all data
        self.model.fit(X, y)

        # Store metrics
        self.metrics = {
            "classifier_accuracy": round(cv_accuracy, 4),
            "classifier_f1_macro": round(cv_f1, 4),
            "n_classes": len(self.label_encoder.classes_),
            "n_samples": len(X),
            "n_features": len(self.feature_columns),
        }

        return self.metrics

    def predict(self, df: pd.DataFrame, feature_engineer: TransactionFeatureEngineer) -> list[dict]:
        """
        Predict categories for new transactions.

        Returns:
            List of dicts with predicted_category and confidence.
        """
        processed = feature_engineer.transform(df)
        X, _ = build_classifier_features(processed)

        # Ensure column order matches training
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_columns]

        probas = self.model.predict_proba(X)
        predictions = self.model.predict(X)
        categories = self.label_encoder.inverse_transform(predictions)

        results = []
        for i, (cat, prob) in enumerate(zip(categories, probas)):
            results.append({
                "predicted_category": cat,
                "confidence": round(float(prob.max()), 4),
            })
        return results

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance scores from the trained model."""
        importances = self.model.feature_importances_
        importance_dict = {
            col: round(float(imp), 4)
            for col, imp in sorted(
                zip(self.feature_columns, importances),
                key=lambda x: x[1],
                reverse=True,
            )
        }
        return importance_dict

    def save(self):
        """Save the trained model, label encoder, and metadata."""
        os.makedirs(SAVE_DIR, exist_ok=True)
        joblib.dump(self.model, os.path.join(SAVE_DIR, "classifier.joblib"))
        joblib.dump(self.label_encoder, os.path.join(SAVE_DIR, "classifier_label_encoder.joblib"))
        joblib.dump(self.feature_columns, os.path.join(SAVE_DIR, "classifier_features.joblib"))
        print(f"Classifier saved to {SAVE_DIR}")

    @classmethod
    def load(cls) -> "SpendingClassifier":
        """Load a trained classifier from disk."""
        instance = cls()
        instance.model = joblib.load(os.path.join(SAVE_DIR, "classifier.joblib"))
        instance.label_encoder = joblib.load(os.path.join(SAVE_DIR, "classifier_label_encoder.joblib"))
        instance.feature_columns = joblib.load(os.path.join(SAVE_DIR, "classifier_features.joblib"))
        return instance
