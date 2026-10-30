from pathlib import Path
from src.classifier import train_and_save

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    metrics = train_and_save(root / "data" / "news.csv", root / "models" / "fake_news_pipeline.joblib")
    print("Training completed")
    for key, value in metrics.items():
        print(f"{key}: {value}")
