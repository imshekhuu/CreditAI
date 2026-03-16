import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings

# Suppress sklearn warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)


def generate_training_data(n_samples=500):

    np.random.seed(42)

    data = []
    labels = []

    for _ in range(n_samples):

        risk_category = np.random.choice([0, 1, 2], p=[0.4, 0.35, 0.25])

        if risk_category == 0:  # Low Risk
            revenue = np.random.uniform(100, 500)
            profit = np.random.uniform(15, 80)
            debt = np.random.uniform(5, 50)
        elif risk_category == 1:  # Medium Risk
            revenue = np.random.uniform(40, 200)
            profit = np.random.uniform(2, 30)
            debt = np.random.uniform(30, 120)
        else:  # High Risk
            revenue = np.random.uniform(5, 80)
            profit = np.random.uniform(-10, 10)
            debt = np.random.uniform(80, 300)

        data.append([revenue, profit, debt])
        labels.append(risk_category)

    X = pd.DataFrame(data, columns=["revenue", "profit", "debt"])
    y = np.array(labels)

    return X, y


def train_model():

    print("[Risk Model] Generating synthetic training data...")
    X, y = generate_training_data(n_samples=500)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )


    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )

    print("[Risk Model] Training Random Forest classifier...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"[Risk Model] Model accuracy: {accuracy:.2%}")

    return model, accuracy



print("[Risk Model] Initializing credit risk model...")
_model, _accuracy = train_model()


def predict_risk(financial_data):


    revenue = financial_data.get("revenue", 0)
    profit = financial_data.get("profit", 0)
    debt = financial_data.get("debt", 0)


    features = pd.DataFrame([[revenue, profit, debt]], columns=["revenue", "profit", "debt"])


    risk_class = int(_model.predict(features)[0])
    probabilities = _model.predict_proba(features)[0]


    risk_map = {0: "Low", 1: "Medium", 2: "High"}
    risk_level = risk_map.get(risk_class, "Unknown")

    risk_probability = float(probabilities[risk_class])

    importances = _model.feature_importances_
    feature_importance = {
        "revenue": round(float(importances[0]), 4),
        "profit": round(float(importances[1]), 4),
        "debt": round(float(importances[2]), 4)
    }

    result = {
        "risk_probability": round(risk_probability, 4),
        "risk_level": risk_level,
        "risk_class": risk_class,
        "confidence": round(risk_probability * 100, 2),
        "model_accuracy": round(_accuracy * 100, 2),
        "feature_importance": feature_importance,
        "all_probabilities": {
            "Low": round(float(probabilities[0]), 4),
            "Medium": round(float(probabilities[1]), 4),
            "High": round(float(probabilities[2]), 4)
        }
    }

    print(f"[Risk Model] Prediction: {risk_level} (confidence: {risk_probability:.2%})")
    return result
