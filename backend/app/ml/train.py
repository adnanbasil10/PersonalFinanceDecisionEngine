"""
Master ML Training Script.
Orchestrates data generation, preprocessing, and training of all models.

Usage:
    cd backend
    python -m app.ml.train
"""

import os
import sys
import json
import time

import pandas as pd

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.ml.data_generator import generate_transactions, save_dataset
from app.ml.preprocessor import TransactionFeatureEngineer, save_preprocessor
from app.ml.classifier import SpendingClassifier
from app.ml.risk_predictor import OverspendRiskPredictor
from app.ml.forecaster import SpendingForecaster


SAVE_DIR = os.path.join(os.path.dirname(__file__), "saved_models")
MONTHLY_INCOME = 75000  # INR


def train_all(data_path: str = None, monthly_income: float = MONTHLY_INCOME):
    """
    Full training pipeline:
    1. Generate/load data
    2. Preprocess features
    3. Train all 3 models
    4. Evaluate and save metrics
    5. Save all models
    """
    start_time = time.time()

    print("=" * 70)
    print("  PERSONAL FINANCE DECISION ENGINE — ML TRAINING PIPELINE")
    print("=" * 70)

    # Step 1: Data
    if data_path and os.path.exists(data_path):
        print(f"\nLoading data from {data_path}...")
        df = pd.read_csv(data_path)
    else:
        print("\nGenerating synthetic transaction data...")
        df = generate_transactions(n_transactions=4000, months=12, monthly_income=monthly_income)
        data_path = save_dataset(df)

    print(f"\nDataset: {len(df)} transactions")

    # Step 2: Preprocessing
    print("\n" + "-" * 40)
    print("STEP 2: Feature Engineering")
    print("-" * 40)
    feature_engineer = TransactionFeatureEngineer()
    feature_engineer.fit(df)
    save_preprocessor(feature_engineer)

    # Step 3: Train Spending Classifier
    classifier = SpendingClassifier()
    classifier_metrics = classifier.train(df, feature_engineer)
    classifier.save()

    # Step 4: Train Risk Predictor
    risk_predictor = OverspendRiskPredictor()
    risk_metrics = risk_predictor.train(df, monthly_income)
    risk_predictor.save()

    # Step 5: Train Forecaster
    forecaster = SpendingForecaster()
    forecast_metrics = forecaster.train(df)
    forecaster.save()

    # Step 6: Save all metrics
    all_metrics = {
        **classifier_metrics,
        **risk_metrics,
        **forecast_metrics,
        "monthly_income": monthly_income,
        "total_transactions": len(df),
        "training_time_seconds": round(time.time() - start_time, 2),
    }

    os.makedirs(SAVE_DIR, exist_ok=True)
    metrics_path = os.path.join(SAVE_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("  TRAINING COMPLETE")
    print("=" * 70)
    print(f"\n  Time elapsed:       {elapsed:.1f}s")
    print(f"  Transactions used:  {len(df)}")
    print(f"\n  CLASSIFIER METRICS:")
    print(f"    Accuracy:         {classifier_metrics.get('classifier_accuracy', 'N/A')}")
    print(f"    F1 (macro):       {classifier_metrics.get('classifier_f1_macro', 'N/A')}")
    print(f"\n  RISK PREDICTOR METRICS:")
    print(f"    AUC-ROC:          {risk_metrics.get('risk_auc_roc', 'N/A')}")
    print(f"    F1:               {risk_metrics.get('risk_f1', 'N/A')}")
    print(f"    Precision:        {risk_metrics.get('risk_precision', 'N/A')}")
    print(f"    Recall:           {risk_metrics.get('risk_recall', 'N/A')}")
    print(f"\n  FORECASTER METRICS:")
    print(f"    Model:            {forecast_metrics.get('model_type', 'N/A')}")
    print(f"    RMSE:             {forecast_metrics.get('forecast_rmse', 'N/A')}")
    print(f"    MAPE:             {forecast_metrics.get('forecast_mape', 'N/A')}%")
    print(f"\n  All models saved to: {SAVE_DIR}")
    print(f"  Metrics saved to:    {metrics_path}")
    print("=" * 70)

    return all_metrics


if __name__ == "__main__":
    # Check for custom data path
    data_path = None
    if len(sys.argv) > 1:
        data_path = sys.argv[1]

    train_all(data_path=data_path)
