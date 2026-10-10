from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Complaint, ComplaintStatus, User, UserRole
from app.schemas import (
    ComplaintCreate, ComplaintResponse, ComplaintDetailResponse,
    BNSSVerifyRequest, BNSSInquiryRequest, ComplaintStatusUpdate
)
from app.auth import get_current_user, require_police_user
from app.utils.bnss_engine import (
    generate_complaint_number, log_timeline,
    calculate_bnss_deadlines, calculate_inquiry_deadline
)

router = APIRouter(prefix="/api/complaints", tags=["Complaints & BNSS 173"])

@router.post("", response_model=ComplaintResponse)
def submit_complaint(
    payload: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    complaint_no = generate_complaint_number(db)
    v_deadline = calculate_bnss_deadlines()

    complaint = Complaint(
        complaint_number=complaint_no,
        citizen_id=current_user.id,
        title=payload.title,
        category=payload.category,
        description=payload.description,
        incident_date=payload.incident_date,
        incident_time=payload.incident_time,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        police_station=payload.police_station,
        accused_details=payload.accused_details,
        witness_details=payload.witness_details,
        is_e_complaint=payload.is_e_complaint if payload.is_e_complaint is not None else True,
        status=ComplaintStatus.SUBMITTED.value,
        verification_deadline=v_deadline
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    # Automatically create the initial audit event in the timeline
    log_timeline(
        db=db,
        complaint_id=complaint.id,
        title="Electronic Complaint Submitted",
        description=f"Complaint lodged electronically under BNSS Section 173(1). 3-day verification window active until {v_deadline.strftime('%d-%b-%Y %I:%M %p')}.",
        event_type="bnss_action",
        actor_name=current_user.full_name
    )

    return complaint

@router.get("", response_model=List[ComplaintResponse])
def get_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    station_filter: Optional[str] = Query(None, alias="station"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Complaint)
    
    # If citizen, restrict to their own complaints
    if current_user.role == UserRole.CITIZEN.value:
        query = query.filter(Complaint.citizen_id == current_user.id)
    elif current_user.role == UserRole.POLICE_OFFICER.value and current_user.police_station:
        # Officer defaults or can filter
        if station_filter:
            query = query.filter(Complaint.police_station.ilike(f"%{station_filter}%"))
    
    if status_filter and status_filter != "all":
        query = query.filter(Complaint.status == status_filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Complaint.complaint_number.ilike(search_pattern)) |
            (Complaint.title.ilike(search_pattern)) |
            (Complaint.category.ilike(search_pattern)) |
            (Complaint.location_name.ilike(search_pattern))
        )

    return query.order_by(Complaint.created_at.desc()).all()

@router.get("/track/{complaint_number}", response_model=ComplaintDetailResponse)
def track_complaint_public(complaint_number: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.complaint_number == complaint_number.strip()).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint number not found")
    return complaint

@router.get("/{complaint_id}", response_model=ComplaintDetailResponse)
def get_complaint_detail(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Access control
    if current_user.role == UserRole.CITIZEN.value and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this complaint")

    return complaint

@router.post("/{complaint_id}/verify", response_model=ComplaintDetailResponse)
def verify_e_signature(
    complaint_id: int,
    req: BNSSVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Only owner citizen or police can verify
    if current_user.role == UserRole.CITIZEN.value and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    complaint.verified_at = datetime.utcnow()
    complaint.status = ComplaintStatus.VERIFIED.value
    db.commit()

    notes = req.notes or f"Verification completed via {req.verification_type} complying with Section 173(1) BNSS (3-day limit)."
    log_timeline(
        db=db,
        complaint_id=complaint.id,
        title="Electronic Verification Completed",
        description=notes,
        event_type="bnss_action",
        actor_name=current_user.full_name
    )

    db.refresh(complaint)
    return complaint

@router.post("/{complaint_id}/preliminary-inquiry", response_model=ComplaintDetailResponse)
def initiate_preliminary_inquiry(
    complaint_id: int,
    req: BNSSInquiryRequest,
    police_user: User = Depends(require_police_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    inq_deadline = calculate_inquiry_deadline()
    complaint.status = ComplaintStatus.PRELIMINARY_INQUIRY.value
    complaint.inquiry_deadline = inq_deadline
    complaint.inquiry_notes = f"Approval Ref: {req.approval_dysp_ref}. Notes: {req.inquiry_notes}. Rec: {req.officer_recommendation}"
    db.commit()

    log_timeline(
        db=db,
        complaint_id=complaint.id,
        title="Preliminary Inquiry Initiated [BNSS Sec 173(3)]",
        description=f"Inquiry ordered with DySP approval ({req.approval_dysp_ref}). 14-day statutory limit active until {inq_deadline.strftime('%d-%b-%Y')}. Recommendation: {req.officer_recommendation}",
        event_type="bnss_action",
        actor_name=police_user.full_name
    )

    db.refresh(complaint)
    return complaint

@router.post("/{complaint_id}/reject", response_model=ComplaintDetailResponse)
def reject_complaint(
    complaint_id: int,
    status_update: ComplaintStatusUpdate,
    police_user: User = Depends(require_police_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    complaint.status = ComplaintStatus.REJECTED.value
    complaint.rejection_reason = status_update.notes or "Non-cognizable / civil dispute. Requisite reason recorded under BNSS 173."
    db.commit()

    log_timeline(
        db=db,
        complaint_id=complaint.id,
        title="Complaint Closed / Non-Cognizable",
        description=f"Reason: {complaint.rejection_reason}. Complainant advised on civil/magistrate remedies.",
        event_type="status_change",
        actor_name=police_user.full_name
    )

    db.refresh(complaint)
    return complaint
