# RETURNSHIELD-AI


## Problem Statement
Returns cost retailers billions due to fraud, abuse, and manual review overhead. Photos/videos submitted during returns are rarely validated against the original SKU, and text reasons are inconsistent. Small and mid-sized stores lack Amazon-grade tooling.

## Solution
**Smart Returns AI** scores each return with explainable signals:

- **Visual Similarity** of the uploaded image vs. the SKU reference (aHash).
- **Image Health** (brightness & sharpness) to spot suspiciously dark/blurred uploads.
- **EXIF Metadata Presence** to flag edited/stripped images.
- **Reason Text Consistency** with order attributes (size/color).
- **Customer History** (return rate).

A weighted **risk score** drives an **auto-approve / manual review / auto-reject** decision. Comes with a web dashboard + API.

## Tech Stack
- **FastAPI** + **Jinja2** (API + simple UI)
- **SQLite + SQLAlchemy**
- **Pillow** for basic vision features
- Pure-Python text heuristics (extensible to LLMs/vision models)

## Run Locally
```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --reload

# Dashboard: http://127.0.0.1:8000/
# Submit Return: http://127.0.0.1:8000/submit
# API Docs (Swagger): http://127.0.0.1:8000/docs
#Review Queue: http://127.0.0.1:8000/review
# Metrics: http://127.0.0.1:8000/metrics
# Case Detail + Override: http://127.0.0.1:8000/returns/{id}
