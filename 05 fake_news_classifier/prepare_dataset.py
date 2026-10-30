import argparse
import pandas as pd
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Normalize a Kaggle fake-news CSV to text,label.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="data/news.csv")
    args = parser.parse_args()
    df = pd.read_csv(args.input)
    # Kaggle's common Fake.csv / True.csv files can be merged first; this helper supports common single-file layouts.
    text_col = next((c for c in ["text", "article", "content", "news"] if c in df.columns), None)
    label_col = next((c for c in ["label", "class", "target"] if c in df.columns), None)
    if text_col is None or label_col is None:
        raise SystemExit(f"Could not identify text/label columns. Found: {list(df.columns)}")
    out = pd.DataFrame({"text": df[text_col].fillna("").astype(str), "label": df[label_col]})
    out["label"] = out["label"].astype(str).str.strip().str.lower().replace({
        "0":"FAKE", "fake":"FAKE", "false":"FAKE",
        "1":"REAL", "real":"REAL", "true":"REAL"
    })
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.output, index=False)
    print(f"Saved {len(out)} rows to {args.output}")

if __name__ == "__main__":
    main()
