# backend/app/seed_data.py
from faker import Faker
import random
import datetime
from app.db import SessionLocal, init_db
from app.models import Complaint, ComplaintCreate
from app.nlp import analyze_text
from app.routing import route_to_department

fake = Faker()
init_db()
db = SessionLocal()

sample_issues = [
    "Water leakage from main pipe near the school.",
    "Streetlight not working for the past week.",
    "Garbage not collected regularly in our area.",
    "Power outage in our street during night.",
    "Road filled with potholes causing accidents.",
    "Sewage overflow creating foul smell.",
    "Bus stop shelter damaged and unsafe.",
    "Electric meter malfunctioning, high bill received.",
    "No proper drainage near market area.",
    "Fire hydrant blocked by garbage near the park.",
]

statuses = ["in_progress", "resolved", "escalated"]

print("🌱 Seeding 100 sample grievances...")
for i in range(100):
    citizen = fake.name()
    text = random.choice(sample_issues)
    # randomize a bit by adding location or urgency keywords
    text += " " + random.choice(["in Anna Nagar.", "near Bus Stand.", "since 2 days.", "urgent attention needed.", "not resolved yet."])
    
    analysis = analyze_text(text)
    dept = analysis["department"]
    urgency = analysis["urgency"]
    reason = analysis["reason"]
    routed_to = route_to_department(dept)

    # Random status
    status = random.choice(statuses)

    # Random created time (within last 15 days)
    created_time = datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(0, 15))

    complaint_data = ComplaintCreate(
        citizen_name=citizen,
        text=text,
        department=dept,
        urgency=urgency,
        routed_to=routed_to,
        reason=reason,
    )

    # manually use model to allow setting created_at and status
    from app.models import ComplaintModel
    c = ComplaintModel(
        citizen_name=citizen,
        text=text,
        department=dept,
        urgency=urgency,
        routed_to=routed_to,
        reason=reason,
        status=status,
        created_at=created_time,
    )
    db.add(c)

db.commit()
db.close()
print("✅ Database seeded successfully with 100 records.")
