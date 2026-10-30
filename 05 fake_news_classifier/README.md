# Fake News Classifier (Python + Machine Learning + Streamlit)

A complete implementation of the supplied project synopsis. It includes text cleaning, TF-IDF unigram/bigram features, a Logistic Regression classifier, held-out evaluation, and an interactive Streamlit app.

## Important limitation
This is a **dataset-trained text-pattern classifier**, not a live fact-checking service. It cannot establish whether a claim is true, check sources, or reliably classify unfamiliar topics. Its output can be wrong and can inherit bias from the training data. Treat the result as a screening signal only.

## Requirements
- Python 3.10 through 3.12 (validated locally with Python 3.12)
- 4 GB RAM recommended
- Windows, Linux, or macOS

## Quick start (Windows)
1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. Open Terminal in that folder.
4. Run:

```bash
py -3.12 -m venv .venv
.venv\\Scripts\\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

5. Prepare a labeled dataset as described below.
6. Train:

```bash
python train.py
```

7. Launch:

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually http://localhost:8501.

## Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python train.py
streamlit run app.py
```

## Dataset format
A small **illustrative demo dataset** is included at `data/news.csv` so the app can be launched immediately. It is synthetic and is only for verifying the workflow; its metrics and predictions are not meaningful evidence of real-world accuracy. For a meaningful model, replace it with a sufficiently large, correctly labeled dataset. The CSV must have exactly these required columns:

| text | label |
|---|---|
| Full article or headline text | REAL |
| Full article or headline text | FAKE |

Accepted labels: `FAKE` / `REAL`, or `0` / `1` (0=FAKE, 1=REAL). Use a properly labeled public dataset such as the Kaggle Fake and Real News dataset. Follow the dataset's license and terms.

For a common single-file Kaggle CSV:
```bash
python prepare_dataset.py --input path/to/news.csv --output data/news.csv
```

If your source provides separate `Fake.csv` and `True.csv` files, merge them first:
```python
import pandas as pd
fake = pd.read_csv("Fake.csv")
real = pd.read_csv("True.csv")
fake["label"] = "FAKE"
real["label"] = "REAL"
pd.concat([fake, real], ignore_index=True)[["text", "label"]].to_csv("data/news.csv", index=False)
```

The dataset should contain both classes, at least 20 usable records (1000+ recommended), and enough examples per class. Avoid duplicate or near-duplicate articles across train/test splits; for rigorous evaluation use a source/time-separated test set.

## Training and evaluation
```bash
python train.py
```
The script saves:
- `models/fake_news_pipeline.joblib`
- `models/fake_news_pipeline.metrics.json`

The app trains automatically on first run if `data/news.csv` exists. The **Retrain model** button retrains after you replace the CSV.

Metrics shown: accuracy, REAL-class precision/recall/F1, and confusion matrix.

## Project structure
```
fake_news_classifier/
├── app.py
├── train.py
├── prepare_dataset.py
├── requirements.txt
├── src/
│   └── classifier.py
├── data/
│   └── news.csv        # add your labeled dataset here
├── models/             # trained model generated here
├── tests/
│   └── test_classifier.py
└── reports/
```

## Troubleshooting
- `streamlit is not recognized`: activate `.venv`, then run `python -m streamlit run app.py`.
- Missing package: run `pip install -r requirements.txt`.
- Dataset column error: ensure columns are named `text` and `label`.
- Not enough rows/classes: provide more labeled examples from both classes.
- Low performance: improve label quality, remove duplicates, use more representative data, and evaluate on unseen sources.

## Synopsis coverage
1. Data acquisition and preprocessing: CSV ingestion, normalization, noise removal.
2. Feature extraction: TF-IDF.
3. Training/evaluation: Logistic Regression classifier and accuracy/precision/recall/F1/confusion matrix.
4. Web GUI: Streamlit input and REAL/FAKE output.
5. Future scope not implemented: BERT/LSTM, multilingual/Hindi support, browser extension, social integrations, URL scraping, and OCR.
