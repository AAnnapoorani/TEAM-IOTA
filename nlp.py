# backend/app/nlp.py
from typing import Dict
import re
import os

# Try to use a small HuggingFace model if internet available.
# If not available, fallback to deterministic rule-based logic.
USE_TRANSFORMER = False
try:
    from transformers import pipeline
    # use a small model to reduce download time - change if necessary
    classifier = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")
    USE_TRANSFORMER = True
except Exception as e:
    # no internet or transformers not installed, fallback
    print("Transformer not available; using rule-based classifier. Reason:", e)
    USE_TRANSFORMER = False

# Department keywords mapping (expand for your demo)
DEPT_KEYWORDS = {
    "Water Supply": ["water", "tap", "leak", "drainage", "sewage"],
    "Sanitation": ["garbage", "trash", "clean", "sweep", "drain", "sewer"],
    "Electricity": ["light", "electric", "power", "meter", "bulb", "streetlight"],
    "Roads & Infrastructure": ["road", "pothole", "bridge", "footpath", "sidewalk"],
    "Health & Safety": ["accident", "injury", "hospital", "danger", "unsafe", "fire"],
    "Public Transport": ["bus", "stop", "train", "metro"],
}

URGENT_WORDS = ["urgent", "danger", "accident", "fire", "hospital", "collapse", "unsafe", "critical"]

def simple_department_from_text(text: str) -> str:
    t = text.lower()
    counts = {}
    for dept, kws in DEPT_KEYWORDS.items():
        for k in kws:
            if k in t:
                counts[dept] = counts.get(dept, 0) + 1
    if counts:
        # return department with max count
        return max(counts.items(), key=lambda x: x[1])[0]
    # fallback general
    return "General Administration"

def predict_urgency(text: str) -> str:
    t = text.lower()
    for w in URGENT_WORDS:
        if re.search(r'\b' + re.escape(w) + r'\b', t):
            return "High"
    # if says "not important" or "small", low:
    if re.search(r'\b(minor|small|not urgent|low priority)\b', t):
        return "Low"
    return "Medium"

def analyze_text(text: str) -> Dict:
    """Return {'department':..., 'urgency':..., 'reason':...}"""
    reason = ""
    # If transformer is available, optionally use sentiment or classification to augment urgency
    if USE_TRANSFORMER:
        try:
            out = classifier(text, top_k=3)
            # out is list of dicts with label & score; for SST-2 labels: POSITIVE/NEGATIVE
            # We'll use negative sentiment + urgent words to boost urgency
            labels = [d["label"] for d in out]
            reason = f"Transformer labels: {labels}"
        except Exception as e:
            reason = f"Transformer failed: {e}"

    department = simple_department_from_text(text)
    urgency = predict_urgency(text)
    return {"department": department, "urgency": urgency, "reason": reason}
