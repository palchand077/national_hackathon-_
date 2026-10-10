import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Numeric, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    POLICE_OFFICER = "police_officer"
    POLICE_ADMIN = "police_admin"

class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    PRELIMINARY_INQUIRY = "preliminary_inquiry"
    FIR_REGISTERED = "fir_registered"
    CLOSED = "closed"
    REJECTED = "rejected"

class FIRStatus(str, enum.Enum):
    REGISTERED = "registered"
    UNDER_INVESTIGATION = "under_investigation"
    CHARGESHEET_FILED = "chargesheet_filed"
    CLOSED = "closed"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=False)
    aadhar_last4 = Column(String(4), nullable=True)
    role = Column(String(50), default=UserRole.CITIZEN.value, index=True)
    badge_number = Column(String(50), nullable=True)
    police_station = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaints = relationship("Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id")
    assigned_firs = relationship("FIR", back_populates="investigating_officer")

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_number = Column(String(50), unique=True, index=True, nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    incident_date = Column(String(50), nullable=False)
    incident_time = Column(String(50), nullable=True)
    location_name = Column(String(255), nullable=False)
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    police_station = Column(String(100), nullable=False, index=True)
    accused_details = Column(Text, nullable=True)
    witness_details = Column(Text, nullable=True)
    status = Column(String(50), default=ComplaintStatus.SUBMITTED.value, index=True)
    is_e_complaint = Column(Boolean, default=True)
    
    # BNSS 173 specific fields
    verification_deadline = Column(DateTime, nullable=True) # 3 days from submission under BNSS 173(1)
    verified_at = Column(DateTime, nullable=True)
    inquiry_deadline = Column(DateTime, nullable=True)      # 14 days under BNSS 173(3)
    inquiry_notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    citizen = relationship("User", back_populates="complaints", foreign_keys=[citizen_id])
    fir = relationship("FIR", back_populates="complaint", uselist=False)
    evidences = relationship("Evidence", back_populates="complaint", cascade="all, delete-orphan")
    timeline = relationship("TimelineEvent", back_populates="complaint", cascade="all, delete-orphan", order_by="TimelineEvent.created_at.desc()")
    ai_analysis = relationship("AIAnalysis", back_populates="complaint", uselist=False, cascade="all, delete-orphan")

class FIR(Base):
    __tablename__ = "firs"

    id = Column(Integer, primary_key=True, index=True)
    fir_number = Column(String(50), unique=True, index=True, nullable=False)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), unique=True, nullable=False)
    police_station = Column(String(100), nullable=False, index=True)
    investigating_officer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bns_sections = Column(Text, nullable=False) # e.g. "BNS Sec 303(2), BNS Sec 318(4)"
    acts_and_sections = Column(Text, nullable=True)
    date_of_occurrence = Column(String(50), nullable=False)
    date_reported = Column(DateTime, default=datetime.utcnow)
    place_of_occurrence = Column(String(255), nullable=False)
    complainant_name = Column(String(150), nullable=False)
    accused_details = Column(Text, nullable=True)
    investigation_summary = Column(Text, nullable=True)
    status = Column(String(50), default=FIRStatus.REGISTERED.value)
    chargesheet_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="fir")
    investigating_officer = relationship("User", back_populates="assigned_firs")

class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    fir_id = Column(Integer, nullable=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False) # image, video, audio, document
    file_size_kb = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    hash_sha256 = Column(String(64), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="evidences")

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), nullable=False, index=True)
    fir_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    event_type = Column(String(50), nullable=False) # bnss_action, status_change, evidence_added, io_assigned, note, chargesheet
    actor_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="timeline")

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"), unique=True, nullable=False, index=True)
    recommended_sections = Column(JSON, nullable=True) # [{"section": "BNS 303(2)", "title": "Theft", "confidence": 0.94}]
    urgency_level = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    duplicate_risk_score = Column(Numeric(5, 2), default=0.00)
    duplicate_candidate_ids = Column(JSON, nullable=True) # list of IDs e.g. ["COMP-2026-098", "COMP-2026-102"]
    extracted_entities = Column(JSON, nullable=True) # {"persons": [], "vehicles": [], "locations": [], "phone_numbers": [], "amounts": []}
    complaint_summary = Column(Text, nullable=True)
    sentiment_emotion = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    complaint = relationship("Complaint", back_populates="ai_analysis")
