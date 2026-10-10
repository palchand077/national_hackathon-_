from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.models import TimelineEvent, Complaint, FIR

def generate_complaint_number(db: Session) -> str:
    year = datetime.utcnow().year
    count = db.query(Complaint).count() + 1
    return f"COMP-{year}-{count:04d}"

def generate_fir_number(db: Session, station: str) -> str:
    year = datetime.utcnow().year
    clean_station = "".join([c.upper() for c in station if c.isalnum()])[:6] or "STN"
    count = db.query(FIR).count() + 1
    return f"FIR/{clean_station}/{year}/{count:04d}"

def log_timeline(
    db: Session,
    complaint_id: int,
    title: str,
    description: str,
    event_type: str,
    actor_name: str,
    fir_id: int = None
) -> TimelineEvent:
    event = TimelineEvent(
        complaint_id=complaint_id,
        fir_id=fir_id,
        title=title,
        description=description,
        event_type=event_type,
        actor_name=actor_name,
        created_at=datetime.utcnow()
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def calculate_bnss_deadlines():
    now = datetime.utcnow()
    # BNSS Section 173(1): Electronic communication must be signed/verified within three days
    verification_deadline = now + timedelta(days=3)
    return verification_deadline

def calculate_inquiry_deadline():
    now = datetime.utcnow()
    # BNSS Section 173(3): Preliminary inquiry must be completed within 14 days
    inquiry_deadline = now + timedelta(days=14)
    return inquiry_deadline
