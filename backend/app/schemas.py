from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

# User Schemas
class UserRegister(BaseModel):
    email: str
    password: str = Field(min_length=6)
    full_name: str
    phone: str
    aadhar_last4: Optional[str] = None
    role: Optional[str] = "citizen"
    badge_number: Optional[str] = None
    police_station: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str
    role: str
    badge_number: Optional[str] = None
    police_station: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Evidence Schemas
class EvidenceResponse(BaseModel):
    id: int
    complaint_id: int
    fir_id: Optional[int] = None
    file_name: str
    file_path: str
    file_type: str
    file_size_kb: int
    description: Optional[str] = None
    hash_sha256: str
    uploaded_by_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Timeline Schemas
class TimelineResponse(BaseModel):
    id: int
    complaint_id: int
    fir_id: Optional[int] = None
    title: str
    description: str
    event_type: str
    actor_name: str
    created_at: datetime

    class Config:
        from_attributes = True

# AI Analysis Schemas
class AIAnalysisIngestRequest(BaseModel):
    complaint_id: int
    recommended_sections: Optional[List[Dict[str, Any]]] = None # [{"section": "BNS 303(2)", "title": "Theft", "confidence": 0.95}]
    urgency_level: Optional[str] = "MEDIUM" # LOW, MEDIUM, HIGH, CRITICAL
    duplicate_risk_score: Optional[float] = 0.0
    duplicate_candidate_ids: Optional[List[str]] = None
    extracted_entities: Optional[Dict[str, Any]] = None # {"suspects": [], "locations": [], "stolen_items": []}
    complaint_summary: Optional[str] = None
    sentiment_emotion: Optional[str] = None

class AIAnalysisResponse(BaseModel):
    id: int
    complaint_id: int
    recommended_sections: Optional[Any] = None
    urgency_level: str
    duplicate_risk_score: float
    duplicate_candidate_ids: Optional[Any] = None
    extracted_entities: Optional[Any] = None
    complaint_summary: Optional[str] = None
    sentiment_emotion: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# FIR Schemas
class FIRCreateRequest(BaseModel):
    complaint_id: int
    police_station: str
    bns_sections: str
    acts_and_sections: Optional[str] = None
    date_of_occurrence: str
    place_of_occurrence: str
    accused_details: Optional[str] = None
    investigation_summary: Optional[str] = None

class FIRStatusUpdate(BaseModel):
    status: str
    investigation_summary: Optional[str] = None
    chargesheet_summary: Optional[str] = None

class FIRResponse(BaseModel):
    id: int
    fir_number: str
    complaint_id: int
    police_station: str
    investigating_officer_id: int
    bns_sections: str
    acts_and_sections: Optional[str] = None
    date_of_occurrence: str
    date_reported: datetime
    place_of_occurrence: str
    complainant_name: str
    accused_details: Optional[str] = None
    investigation_summary: Optional[str] = None
    status: str
    chargesheet_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Complaint Schemas
class ComplaintCreate(BaseModel):
    title: str
    category: str
    description: str
    incident_date: str
    incident_time: Optional[str] = None
    location_name: str
    latitude: float
    longitude: float
    police_station: str
    accused_details: Optional[str] = None
    witness_details: Optional[str] = None
    is_e_complaint: Optional[bool] = True

class BNSSVerifyRequest(BaseModel):
    verification_type: str = "Aadhaar_OTP_Digital_Signature" # or "Physical_Station_Signature"
    notes: Optional[str] = None

class BNSSInquiryRequest(BaseModel):
    officer_recommendation: str
    inquiry_notes: str
    approval_dysp_ref: Optional[str] = "DYSP/PERM/BNSS173(3)/2026/04"

class ComplaintStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class ComplaintResponse(BaseModel):
    id: int
    complaint_number: str
    citizen_id: int
    title: str
    category: str
    description: str
    incident_date: str
    incident_time: Optional[str] = None
    location_name: str
    latitude: float
    longitude: float
    police_station: str
    accused_details: Optional[str] = None
    witness_details: Optional[str] = None
    status: str
    is_e_complaint: bool
    verification_deadline: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    inquiry_deadline: Optional[datetime] = None
    inquiry_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ComplaintDetailResponse(ComplaintResponse):
    citizen: Optional[UserResponse] = None
    fir: Optional[FIRResponse] = None
    evidences: List[EvidenceResponse] = []
    timeline: List[TimelineResponse] = []
    ai_analysis: Optional[AIAnalysisResponse] = None

# Metrics & GIS Schemas
class GISCrimeMarker(BaseModel):
    id: int
    complaint_number: str
    title: str
    category: str
    latitude: float
    longitude: float
    location_name: str
    police_station: str
    status: str
    urgency_level: Optional[str] = "MEDIUM"
    incident_date: str

class DashboardMetrics(BaseModel):
    total_complaints: int
    pending_verification: int # Under BNSS 173 3-day window
    under_preliminary_inquiry: int # Under BNSS 173 14-day inquiry
    firs_registered: int
    cases_resolved: int
    critical_alerts: int
