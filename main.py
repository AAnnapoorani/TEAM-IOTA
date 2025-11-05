# backend/app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.db import init_db, SessionLocal
from app.models import Complaint, ComplaintCreate, ComplaintRead, ComplaintStatusEnum
from app.nlp import analyze_text
from app.routing import ROUTING_TABLE, route_to_department
import threading
import time
import datetime

app = FastAPI(title="SGCRS Prototype API")

# initialize DB (creates sqlite file)
init_db()

from app.models import ComplaintModel
from app.seed_data import fake, analyze_text, route_to_department
from sqlalchemy.orm import Session
db = SessionLocal()
count = db.query(ComplaintModel).count()
if count == 0:
    import app.seed_data  # auto-run seeder
db.close()


# background escalator
ESCALATION_SECONDS = 60 * 60 * 24 * 2  # 48 hours -> for demo you can set to 120 for 2 minutes
CHECK_INTERVAL = 30  # seconds

class AnalyzeRequest(BaseModel):
    citizen_name: Optional[str] = "Anonymous"
    text: str

@app.post("/analyze", response_model=ComplaintRead)
def analyze_and_create(req: AnalyzeRequest):
    """Analyze text, classify department & urgency, route and store complaint"""
    analysis = analyze_text(req.text)
    department = analysis["department"]
    urgency = analysis["urgency"]
    reason = analysis.get("reason", "")

    routed_to = route_to_department(department)

    # store complaint in DB
    db = SessionLocal()
    complaint = ComplaintCreate(
        citizen_name=req.citizen_name,
        text=req.text,
        department=department,
        urgency=urgency,
        routed_to=routed_to,
        reason=reason
    )
    c = Complaint.create(db, complaint)
    db.close()
    return c

@app.get("/complaints", response_model=List[ComplaintRead])
def list_complaints():
    db = SessionLocal()
    items = Complaint.list_all(db)
    db.close()
    return items

@app.get("/complaints/{complaint_id}", response_model=ComplaintRead)
def get_complaint(complaint_id: int):
    db = SessionLocal()
    c = Complaint.get(db, complaint_id)
    db.close()
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return c

@app.post("/complaints/{complaint_id}/update_status", response_model=ComplaintRead)
def update_status(complaint_id: int, status: ComplaintStatusEnum):
    db = SessionLocal()
    c = Complaint.get(db, complaint_id)
    if not c:
        db.close()
        raise HTTPException(status_code=404, detail="Complaint not found")
    updated = Complaint.update_status(db, complaint_id, status)
    db.close()
    return updated

# background escalator thread implementation
def escalator_loop():
    while True:
        db = SessionLocal()
        try:
            now = datetime.datetime.utcnow()
            all_open = Complaint.list_open(db)
            for c in all_open:
                created = c.created_at
                delta = now - created
                if delta.total_seconds() > ESCALATION_SECONDS and c.status == ComplaintStatusEnum.in_progress:
                    Complaint.update_status(db, c.id, ComplaintStatusEnum.escalated)
                    print(f"[Escalator] Complaint {c.id} escalated (delta {delta})")
        except Exception as e:
            print("Escalator error:", e)
        finally:
            db.close()
        time.sleep(CHECK_INTERVAL)

@app.on_event("startup")
def start_background_tasks():
    t = threading.Thread(target=escalator_loop, daemon=True)
    t.start()
    print("Escalator thread started.")
