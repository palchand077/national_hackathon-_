from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Complaint, FIR, ComplaintStatus, FIRStatus, AIAnalysis
from app.schemas import DashboardMetrics, GISCrimeMarker

router = APIRouter(prefix="/api/stats", tags=["Dashboard Metrics & GIS Map Data"])

@router.get("/dashboard", response_model=DashboardMetrics)
def get_dashboard_metrics(db: Session = Depends(get_db)):
    total_complaints = db.query(Complaint).count()
    pending_verification = db.query(Complaint).filter(Complaint.status == ComplaintStatus.SUBMITTED.value).count()
    under_inquiry = db.query(Complaint).filter(Complaint.status == ComplaintStatus.PRELIMINARY_INQUIRY.value).count()
    firs_count = db.query(FIR).count()
    cases_resolved = db.query(FIR).filter(FIR.status == FIRStatus.CLOSED.value).count() + \
                     db.query(Complaint).filter(Complaint.status == ComplaintStatus.CLOSED.value).count()
    critical_alerts = db.query(AIAnalysis).filter(AIAnalysis.urgency_level.in_(["HIGH", "CRITICAL"])).count()

    return DashboardMetrics(
        total_complaints=total_complaints,
        pending_verification=pending_verification,
        under_preliminary_inquiry=under_inquiry,
        firs_registered=firs_count,
        cases_resolved=cases_resolved,
        critical_alerts=critical_alerts
    )

@router.get("/crime-map", response_model=List[GISCrimeMarker])
def get_gis_crime_markers(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).all()
    markers = []
    for c in complaints:
        urgency = c.ai_analysis.urgency_level if c.ai_analysis else "MEDIUM"
        markers.append(GISCrimeMarker(
            id=c.id,
            complaint_number=c.complaint_number,
            title=c.title,
            category=c.category,
            latitude=float(c.latitude),
            longitude=float(c.longitude),
            location_name=c.location_name,
            police_station=c.police_station,
            status=c.status,
            urgency_level=urgency,
            incident_date=c.incident_date
        ))
    return markers
