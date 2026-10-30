import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from classifier import clean_text, normalize_label

def test_clean_text():
    assert clean_text("HELLO!!! https://example.com World") == "hello world"

def test_labels():
    assert normalize_label("fake") == "FAKE"
    assert normalize_label("1") == "REAL"

def test_train_predict_pipeline(tmp_path):
    import pandas as pd
    from classifier import train_and_save, load_or_train, predict_text
    data = tmp_path / 'news.csv'
    rows = []
    for i in range(12):
        rows.append({'text': f'Unverified viral rumour claims miracle secret cure number {i}', 'label': 'FAKE'})
        rows.append({'text': f'Research institute publishes peer reviewed scientific study number {i}', 'label': 'REAL'})
    pd.DataFrame(rows).to_csv(data, index=False)
    model = tmp_path / 'model.joblib'
    metrics = train_and_save(data, model)
    pipeline, loaded_metrics, _ = load_or_train(data, model)
    label, confidence, probabilities = predict_text(pipeline, 'A viral rumour claims a secret miracle cure')
    assert label in {'FAKE', 'REAL'}
    assert 0 <= confidence <= 1
    assert set(probabilities) == {'FAKE', 'REAL'}
    assert metrics['total_rows'] == 24
    assert loaded_metrics['accuracy'] >= 0
