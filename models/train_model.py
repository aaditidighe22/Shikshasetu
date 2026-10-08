"""
ShikshaSetu AI - ML Model Training
Trains a Random Forest classifier on synthetic student data to predict learning status.
Labels: Strong | Moderate | Needs Support

NOTE: This model is trained on synthetic/demo data for prototype purposes.
Results should not be interpreted as real-world educational effectiveness.
"""

import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix
)
import joblib

MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, "learning_gap_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.pkl")
DATA_PATH = os.path.join(MODEL_DIR, "..", "data", "ml_training_data.csv")

FEATURE_COLUMNS = [
    "prev_score",
    "current_score",
    "correct_answers",
    "incorrect_answers",
    "avg_time_per_question",
    "topic_score",
    "easy_correct_pct",
    "medium_correct_pct",
    "hard_correct_pct",
    "num_attempts",
    "prev_improvement",
]
TARGET_COLUMN = "learning_status"


def train_and_save_model():
    """Load data, train Random Forest, save model + encoder, and print evaluation."""
    print("=" * 60)
    print("ShikshaSetu AI - ML Model Training")
    print("=" * 60)

    # Load dataset
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Training data not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    print(f"\n[OK] Dataset loaded: {len(df)} samples")
    print(f"  Class distribution:\n{df[TARGET_COLUMN].value_counts().to_string()}")

    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    print(f"\n[OK] Label classes: {list(le.classes_)}")

    # Train / test split (80/20 stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    print(f"  Train size: {len(X_train)}, Test size: {len(X_test)}")

    # Train Random Forest
    print("\n[...] Training Random Forest Classifier ...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "=" * 60)
    print("MODEL EVALUATION (on held-out test set)")
    print("=" * 60)
    print(f"Accuracy: {acc:.4f} ({acc*100:.1f}%)")
    print("\nClassification Report:")
    print(report)
    print("Confusion Matrix (rows=actual, cols=predicted):")
    print(f"Classes: {list(le.classes_)}")
    print(cm)

    # Feature importance
    fi = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS)
    fi_sorted = fi.sort_values(ascending=False)
    print("\nTop Feature Importances:")
    for feat, imp in fi_sorted.items():
        bar = "|" * int(imp * 40)
        print(f"  {feat:<28} {imp:.4f}  {bar}")

    # Save model and encoder
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"\n[SAVED] Model   -> {MODEL_PATH}")
    print(f"[SAVED] Encoder -> {ENCODER_PATH}")
    print("\n[NOTE] Prototype ML results are based on synthetic/demo")
    print("   assessment data and should not be interpreted as real-world")
    print("   educational effectiveness.")
    print("=" * 60)

    return model, le, acc, report, cm


def load_model():
    """Load trained model and label encoder. Returns (model, encoder) or (None, None)."""
    if os.path.exists(MODEL_PATH) and os.path.exists(ENCODER_PATH):
        model = joblib.load(MODEL_PATH)
        le = joblib.load(ENCODER_PATH)
        return model, le
    return None, None


def predict_learning_status(features: dict):
    """
    Predict learning status for a single student.

    features dict keys should match FEATURE_COLUMNS.
    Returns: (status_label, confidence_pct) or fallback if model unavailable.
    """
    model, le = load_model()
    if model is None:
        # Fallback: rule-based classification
        score = features.get("current_score", features.get("topic_score", 50))
        if score >= 80:
            return "Strong", 85.0
        elif score >= 60:
            return "Moderate", 75.0
        else:
            return "Needs Support", 80.0

    # Build feature vector in correct order (use DataFrame to preserve feature names)
    import pandas as pd
    X = pd.DataFrame([[features.get(col, 0) for col in FEATURE_COLUMNS]],
                     columns=FEATURE_COLUMNS)
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    label = le.inverse_transform([pred])[0]
    confidence = round(max(proba) * 100, 1)
    return label, confidence


def predict_from_score(score_pct, topic_score=None, num_attempts=1, prev_score=None):
    """
    Convenience wrapper: predict status from a percentage score.
    Fills missing features with reasonable defaults.
    """
    topic_score = topic_score if topic_score is not None else score_pct
    prev_score = prev_score if prev_score is not None else max(score_pct - 5, 0)
    total_q = 25
    correct = round(score_pct / 100 * total_q)
    incorrect = total_q - correct

    features = {
        "prev_score": prev_score,
        "current_score": score_pct,
        "correct_answers": correct,
        "incorrect_answers": incorrect,
        "avg_time_per_question": 45,
        "topic_score": topic_score,
        "easy_correct_pct": min(score_pct + 10, 100),
        "medium_correct_pct": score_pct,
        "hard_correct_pct": max(score_pct - 15, 0),
        "num_attempts": num_attempts,
        "prev_improvement": score_pct - prev_score,
    }
    return predict_learning_status(features)


if __name__ == "__main__":
    train_and_save_model()
