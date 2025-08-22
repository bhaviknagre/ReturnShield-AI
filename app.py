import os
from fastapi import FastAPI, Depends, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from db import Base, engine, get_db
from models import Customer, Order, ReturnRequest
from schemas import ReturnCreate, ReturnOut
from utils.image_analysis import (
    image_similarity,
    brightness_score,
    blur_score,
    exif_metadata_score,
)
from utils.nlp import text_consistency_score
from sample_data import seed

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
CATALOG_DIR = os.path.join(os.path.dirname(__file__), "catalog_images")

app = FastAPI(title="Smart Returns AI", version="1.1.0")

# --- Tunable thresholds (adjust for your business) ---
AUTO_APPROVE_THRESHOLD = float(os.getenv("AUTO_APPROVE_THRESHOLD", "0.35"))
AUTO_REJECT_THRESHOLD = float(os.getenv("AUTO_REJECT_THRESHOLD", "0.75"))

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
    name="static",
)
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# Initialize DB
Base.metadata.create_all(bind=engine)
# Seed
with next(get_db()) as db:
    seed(db)


def compute_customer_history(customer: Customer) -> float:
    if not customer or (customer.total_orders or 0) == 0:
        return 0.5
    rate = (customer.total_returns or 0) / max(1, customer.total_orders)
    # Lower return rate -> better score
    return float(max(0.0, min(1.0, 1.0 - rate)))


def decision_from_risk(risk: float) -> str:
    if risk < AUTO_APPROVE_THRESHOLD:
        return "auto_approve"
    if risk > AUTO_REJECT_THRESHOLD:
        return "auto_reject"
    return "manual_review"


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    returns = (
        db.query(ReturnRequest)
        .order_by(ReturnRequest.created_at.desc())
        .limit(25)
        .all()
    )
    total = db.query(ReturnRequest).count()
    auto_approve = (
        db.query(ReturnRequest).filter(ReturnRequest.decision == "auto_approve").count()
    )
    auto_reject = (
        db.query(ReturnRequest).filter(ReturnRequest.decision == "auto_reject").count()
    )
    manual = total - auto_approve - auto_reject
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "returns": returns,
            "stats": {
                "total": total,
                "auto_approve": auto_approve,
                "auto_reject": auto_reject,
                "manual": manual,
            },
        },
    )


@app.get("/submit", response_class=HTMLResponse)
def submit_form(request: Request):
    return templates.TemplateResponse("submit_return.html", {"request": request})


@app.post("/api/returns", response_model=ReturnOut)
async def create_return(
    order_id: str = Form(...),
    customer_email: str = Form(...),
    customer_name: Optional[str] = Form(None),
    sku: str = Form(...),
    reason: str = Form(...),
    size: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    # Lookup or create customer
    customer = db.query(Customer).filter_by(email=customer_email).first()
    if not customer:
        customer = Customer(
            email=customer_email,
            name=customer_name or "Guest",
            total_orders=1,
            total_returns=0,
        )
        db.add(customer)
        db.flush()

    # Create order record if missing
    order = db.query(Order).filter_by(order_id=order_id).first()
    if not order:
        order = Order(
            order_id=order_id,
            customer_id=customer.id,
            sku=sku,
            size=size,
            color=color,
            status="delivered",
        )
        db.add(order)
        db.flush()

    # Save uploaded image
    image_path = None
    if image:
        # Create directories if they don't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        os.makedirs(CATALOG_DIR, exist_ok=True)

        # Get file extension from original filename
        _, ext = os.path.splitext(image.filename)
        if not ext:
            ext = ".jpg"  # Default extension if none provided

        # Create safe filename with proper extension
        safe_filename = f"{order_id}{ext}".replace(" ", "_")
        dest = os.path.join(UPLOAD_DIR, safe_filename)

        # Save the file
        content = await image.read()
        with open(dest, "wb") as f:
            f.write(content)

        # Validate that it's a valid image file
        try:
            from PIL import Image

            img = Image.open(dest)
            img.verify()  # Verify it's a valid image
            image_path = dest
        except Exception:
            if os.path.exists(dest):
                os.remove(dest)  # Clean up invalid file
            raise HTTPException(status_code=400, detail="Invalid image file")

    # Compute features
    ref_path = os.path.join(CATALOG_DIR, f"{sku}.jpg")
    sim = image_similarity(image_path, ref_path) if image_path else 0.0
    bright = brightness_score(image_path) if image_path else 0.0
    blur = blur_score(image_path) if image_path else 0.0
    meta = exif_metadata_score(image_path) if image_path else 0.3
    text_score = text_consistency_score(
        reason, {"size": order.size, "color": order.color}
    )
    hist = compute_customer_history(customer)

    # Risk scoring (weighted)
    # Low similarity, very low brightness, very low blur, low metadata, low text consistency, poor history -> higher risk
    risk = (
        (1.0 - sim) * 0.35
        + (0.5 - abs(bright - 0.5)) * 0.10  # prefer mid brightness
        + (1.0 - blur) * 0.10
        + (1.0 - meta) * 0.10
        + (1.0 - text_score) * 0.20
        + (1.0 - hist) * 0.15
    )
    risk = float(max(0.0, min(1.0, risk)))
    decision = decision_from_risk(risk)

    ret = ReturnRequest(
        order_id=order_id,
        customer_id=customer.id,
        sku=sku,
        reason=reason,
        image_path=image_path,
        similarity_score=sim,
        brightness=bright,
        blur=blur,
        metadata_score=meta,
        text_consistency=text_score,
        customer_history=hist,
        risk_score=risk,
        decision=decision,
    )
    db.add(ret)

    # Update customer stats
    customer.total_returns = (customer.total_returns or 0) + 1
    db.commit()
    db.refresh(ret)

    return ret


@app.get("/review", response_class=HTMLResponse)
def review_queue(request: Request, db: Session = Depends(get_db)):
    pending = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.decision == "manual_review")
        .order_by(ReturnRequest.created_at.asc())
        .all()
    )
    return templates.TemplateResponse(
        "review_queue.html", {"request": request, "pending": pending}
    )


@app.post("/returns/{rid}/override")
async def override_decision(rid: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    new_decision = form.get("decision")
    notes = form.get("notes")
    ret = db.query(ReturnRequest).get(rid)
    if not ret:
        return HTMLResponse("Not found", status_code=404)
    if new_decision not in {"auto_approve", "manual_review", "auto_reject"}:
        return HTMLResponse("Invalid decision", status_code=400)
    ret.decision = new_decision
    # append notes
    if notes:
        if ret.notes:
            ret.notes += f"\nOVERRIDE: {notes}"
        else:
            ret.notes = f"OVERRIDE: {notes}"
    db.commit()
    return RedirectResponse(url=f"/returns/{rid}", status_code=303)


@app.get("/metrics", response_class=HTMLResponse)
def metrics(request: Request, db: Session = Depends(get_db)):
    total = db.query(ReturnRequest).count()
    aa = (
        db.query(ReturnRequest).filter(ReturnRequest.decision == "auto_approve").count()
    )
    ar = db.query(ReturnRequest).filter(ReturnRequest.decision == "auto_reject").count()
    mr = (
        db.query(ReturnRequest)
        .filter(ReturnRequest.decision == "manual_review")
        .count()
    )
    avg_risk = 0.0
    if total:
        from sqlalchemy import func

        avg_risk = db.query(func.avg(ReturnRequest.risk_score)).scalar() or 0.0
    return templates.TemplateResponse(
        "metrics.html",
        {
            "request": request,
            "stats": {
                "total": total,
                "auto_approve": aa,
                "auto_reject": ar,
                "manual": mr,
                "avg_risk": avg_risk,
            },
        },
    )


@app.get("/returns/{rid}", response_class=HTMLResponse)
def return_detail(rid: int, request: Request, db: Session = Depends(get_db)):
    ret = db.query(ReturnRequest).get(rid)
    if not ret:
        return HTMLResponse("Not found", status_code=404)
    return templates.TemplateResponse(
        "return_detail.html", {"request": request, "ret": ret}
    )
