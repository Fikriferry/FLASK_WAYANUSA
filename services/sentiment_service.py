import joblib
import os
import re

# =========================
# PATH SETUP
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ml_models", "sentiment_model.pkl")
VECT_PATH  = os.path.join(BASE_DIR, "ml_models", "tfidf_vectorizer.pkl")

# =========================
# LOAD MODEL (ONCE)
# =========================
try:
    model = joblib.load(MODEL_PATH)
    vectorizer = joblib.load(VECT_PATH)
    print("✅ Sentiment model loaded")
except Exception as e:
    print("❌ Gagal load sentiment model:", e)
    model = None
    vectorizer = None


# =========================
# TEXT PREPROCESSING
# =========================
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http\S+", "", text)        # hapus URL
    text = re.sub(r"[^a-zA-Z\s]", "", text)    # hapus simbol
    text = re.sub(r"\s+", " ", text).strip()   # rapikan spasi
    return text


# =========================
# PREDICT SENTIMENT
# =========================
def predict_sentiment(text: str):
    if not text or not text.strip():
        return "netral", 0.0

    if model is None or vectorizer is None:
        return "netral", 0.0

    try:
        cleaned_text = clean_text(text)

        text_vec = vectorizer.transform([cleaned_text])

        label = model.predict(text_vec)[0]
        confidence = model.predict_proba(text_vec).max()

        # Jika model numeric → map ke label
        if isinstance(label, (int, float)):
            label_map = {
                0: "negatif",
                1: "netral",
                2: "positif"
            }
            label = label_map.get(label, "netral")

        return label, round(float(confidence), 3)

    except Exception as e:
        print("⚠️ Sentiment prediction error:", e)
        return "netral", 0.0