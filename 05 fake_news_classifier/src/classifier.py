from pathlib import Path
import json
import re
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def clean_text(value):
    value = str(value or "").lower()
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value

def normalize_label(value):
    v = str(value).strip().lower()
    if v in {"fake", "false", "0", "misleading"}:
        return "FAKE"
    if v in {"real", "true", "1", "genuine"}:
        return "REAL"
    raise ValueError(f"Unsupported label: {value!r}. Use FAKE/REAL or 0/1.")

def load_dataset(path):
    df = pd.read_csv(path)
    if "text" not in df.columns or "label" not in df.columns:
        raise ValueError("Dataset must contain 'text' and 'label' columns.")
    df = df[["text", "label"]].dropna()
    df["text"] = df["text"].map(clean_text)
    df["label"] = df["label"].map(normalize_label)
    df = df[df["text"].str.len() >= 10].drop_duplicates(subset=["text"])
    if len(df) < 20:
        raise ValueError("At least 20 usable rows are required; 1000+ labeled examples are recommended.")
    if df["label"].nunique() != 2:
        raise ValueError("Dataset must contain both FAKE and REAL examples.")
    if df["label"].value_counts().min() < 2:
        raise ValueError("Each class must have at least two examples.")
    return df

def build_pipeline():
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            preprocessor=clean_text, stop_words="english",
            max_df=0.98, min_df=1, ngram_range=(1, 2),
            max_features=150000, sublinear_tf=True
        )),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ])

def train_and_save(data_path, model_path):
    df = load_dataset(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    labels = ["FAKE", "REAL"]
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, pos_label="REAL", zero_division=0)),
        "recall": float(recall_score(y_test, predictions, pos_label="REAL", zero_division=0)),
        "f1": float(f1_score(y_test, predictions, pos_label="REAL", zero_division=0)),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=labels).tolist(),
        "test_rows": int(len(y_test)),
        "total_rows": int(len(df))
    }
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    model_path.with_suffix(".metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics

def load_or_train(data_path, model_path):
    model_path = Path(model_path)
    metrics_path = model_path.with_suffix(".metrics.json")
    if model_path.exists():
        pipeline = joblib.load(model_path)
        metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
        return pipeline, metrics, "user-provided dataset" if Path(data_path).exists() else "bundled demo model"
    if not Path(data_path).exists():
        raise FileNotFoundError("No trained model or data/news.csv found. See README.md.")
    metrics = train_and_save(data_path, model_path)
    return joblib.load(model_path), metrics, "data/news.csv"

def predict_text(pipeline, text):
    prediction = pipeline.predict([text])[0]
    probabilities = {}
    raw = pipeline.predict_proba([text])[0]
    probabilities = {str(k): float(v) for k, v in zip(pipeline.classes_, raw)}
    confidence = probabilities.get(str(prediction), max(probabilities.values()))
    return prediction, float(confidence), probabilities
