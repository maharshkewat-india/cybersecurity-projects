from pathlib import Path
import sys
import streamlit as st
import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from classifier import load_or_train, predict_text, load_dataset, train_and_save

st.set_page_config(page_title="Fake News Classifier", page_icon="📰", layout="wide")
st.markdown("""
<style>
.main {background:#f7f9fc}
.block-container {padding-top:2rem; max-width:1100px}
.hero {padding:1.4rem 1.6rem; border-radius:16px; background:linear-gradient(120deg,#eaf2ff,#f4efff); margin-bottom:1rem}
.small-muted {color:#64748b;font-size:.9rem}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>📰 Fake News Classifier</h1><p>Machine learning + NLP + TF-IDF + Streamlit</p><span class="small-muted">A dataset-trained text classifier for educational screening—not a fact-checking authority.</span></div>', unsafe_allow_html=True)
model_path = ROOT / "models" / "fake_news_pipeline.joblib"
data_path = ROOT / "data" / "news.csv"

@st.cache_resource
def get_model():
    return load_or_train(data_path, model_path)

try:
    pipeline, metrics, dataset_kind = get_model()
except Exception as exc:
    st.error(f"Model could not be loaded: {exc}")
    st.info("Check the README setup instructions, then click Rerun.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["🔎 Classify news", "📊 Model performance", "📁 Dataset & retraining"])
with tab1:
    st.subheader("Check a headline or article")
    sample = "Scientists announce a new public health study after reviewing evidence from several hospitals."
    news_text = st.text_area("Paste news text", value="", height=190, placeholder="Paste the complete headline or article here...")
    c1, c2 = st.columns([1, 4])
    with c1:
        classify = st.button("Classify text", type="primary", width="stretch")
    with c2:
        st.caption("Longer, complete article text generally provides more useful signals than a short headline.")
    if classify:
        if len(news_text.strip()) < 20:
            st.warning("Please enter at least 20 characters for a more meaningful prediction.")
        else:
            label, confidence, probabilities = predict_text(pipeline, news_text)
            if label == "REAL":
                st.success(f"Prediction: {label}")
            else:
                st.error(f"Prediction: {label}")
            st.metric("Model confidence", f"{confidence:.1%}")
            st.progress(float(confidence))
            st.caption("Confidence is the model's estimated class probability, not proof that the story is true or false.")
            st.write("Class probabilities")
            st.bar_chart(pd.DataFrame({"Probability": probabilities}).T)
            st.warning("Always verify important claims with reputable independent sources. This model can make mistakes and may reflect dataset bias.")
with tab2:
    st.subheader("Evaluation summary")
    st.caption(f"Active dataset: {dataset_kind}")
    if metrics:
        cols = st.columns(4)
        for col, key, title in zip(cols, ["accuracy", "precision", "recall", "f1"], ["Accuracy", "Precision", "Recall", "F1 score"]):
            col.metric(title, f"{metrics.get(key, 0):.3f}")
        st.write("Confusion matrix (rows = actual, columns = predicted; class order FAKE, REAL)")
        cm = metrics.get("confusion_matrix", [[0,0],[0,0]])
        st.dataframe(pd.DataFrame(cm, index=["Actual FAKE","Actual REAL"], columns=["Predicted FAKE","Predicted REAL"]), width="stretch")
        st.caption("Metrics are calculated on a held-out test split. They are only as representative as the supplied dataset.")
    else:
        st.info("Evaluation metrics will appear after a dataset has been trained.")
with tab3:
    st.subheader("Dataset")
    st.write("Expected CSV columns: **text** and **label**. Labels can be FAKE/REAL or 0/1. A Kaggle dataset with title/text/label columns can be normalized using the included preparation script.")
    st.code("python prepare_dataset.py --input path/to/kaggle_news.csv --output data/news.csv", language="bash")
    st.write(f"Current dataset file: `{data_path}`")
    if data_path.exists():
        try:
            df = pd.read_csv(data_path)
            st.write(f"Rows: {len(df):,}")
            st.dataframe(df.head(8), width="stretch")
        except Exception as e:
            st.error(f"Could not read dataset: {e}")
    if st.button("Retrain model from data/news.csv"):
        try:
            with st.spinner("Training and evaluating model..."):
                new_metrics = train_and_save(data_path, model_path)
            get_model.clear()
            st.success(f"Training complete. Test accuracy: {new_metrics['accuracy']:.3f}. Reload the page.")
        except Exception as e:
            st.error(f"Training failed: {e}")

st.divider()
st.caption("Project based on the supplied synopsis: data acquisition/pre-processing, TF-IDF feature extraction, ML training/evaluation, and Streamlit GUI.")
