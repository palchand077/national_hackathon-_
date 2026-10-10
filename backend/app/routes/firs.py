from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FIR, Complaint, ComplaintStatus, FIRStatus, User, UserRole
from app.schemas import FIRCreateRequest, FIRStatusUpdate, FIRResponse
from app.auth import get_current_user, require_police_user
from app.utils.bnss_engine import generate_fir_number, log_timeline
from app.utils.report_gen import generate_fir_html_report

router = APIRouter(prefix="/api/firs", tags=["FIR Management"])

@router.post("", response_model=FIRResponse)
def register_fir(
    payload: FIRCreateRequest,
    police_user: User = Depends(require_police_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Associated Complaint not found")

    existing_fir = db.query(FIR).filter(FIR.complaint_id == payload.complaint_id).first()
    if existing_fir:
        raise HTTPException(status_code=400, detail=f"FIR already registered: {existing_fir.fir_number}")

    fir_no = generate_fir_number(db, payload.police_station)

    new_fir = FIR(
        fir_number=fir_no,
        complaint_id=complaint.id,
        police_station=payload.police_station,
        investigating_officer_id=police_user.id,
        bns_sections=payload.bns_sections,
        acts_and_sections=payload.acts_and_sections or "Bharatiya Nyaya Sanhita, 2023 (BNS)",
        date_of_occurrence=payload.date_of_occurrence,
        date_reported=datetime.utcnow(),
        place_of_occurrence=payload.place_of_occurrence,
        complainant_name=complaint.citizen.full_name if complaint.citizen else "Complainant",
        accused_details=payload.accused_details or complaint.accused_details,
        investigation_summary=payload.investigation_summary,
        status=FIRStatus.REGISTERED.value
    )
    db.add(new_fir)

    # Update Complaint status
    complaint.status = ComplaintStatus.FIR_REGISTERED.value
    db.commit()
    db.refresh(new_fir)

    # Log Timeline Event
    log_timeline(
        db=db,
        complaint_id=complaint.id,
        fir_id=new_fir.id,
        title="Official FIR Registered",
        description=f"FIR {fir_no} registered under BNSS Sec 173. Applicable sections: {payload.bns_sections}. IO Assigned: {police_user.full_name}.",
        event_type="fir_generated",
        actor_name=police_user.full_name
    )

    return new_fir

@router.get("", response_model=List[FIRResponse])
def get_all_firs(
    station: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FIR)
    if current_user.role == UserRole.CITIZEN.value:
        # Join complaint to filter only citizen's FIRs
        query = query.join(Complaint).filter(Complaint.citizen_id == current_user.id)
    else:
        if station:
            query = query.filter(FIR.police_station.ilike(f"%{station}%"))
        if status_filter and status_filter != "all":
            query = query.filter(FIR.status == status_filter)

    return query.order_by(FIR.created_at.desc()).all()

@router.get("/{fir_id}", response_model=FIRResponse)
def get_fir_detail(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    
    if current_user.role == UserRole.CITIZEN.value:
        if fir.complaint.citizen_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized")

    return fir

@router.patch("/{fir_id}/status", response_model=FIRResponse)
def update_fir_status(
    fir_id: int,
    update_data: FIRStatusUpdate,
    police_user: User = Depends(require_police_user),
    db: Session = Depends(get_db)
):
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    fir.status = update_data.status
    if update_data.investigation_summary:
        fir.investigation_summary = update_data.investigation_summary
    if update_data.chargesheet_summary:
        fir.chargesheet_summary = update_data.chargesheet_summary

    db.commit()

    # Timeline event
    log_timeline(
        db=db,
        complaint_id=fir.complaint_id,
        fir_id=fir.id,
        title=f"FIR Status Updated to '{update_data.status}'",
        description=f"Summary: {update_data.investigation_summary or update_data.chargesheet_summary or 'Investigation update logged.'}",
        event_type="status_change",
        actor_name=police_user.full_name
    )

    db.refresh(fir)
    return fir

@router.get("/{fir_id}/report")
def view_fir_report(
    fir_id: int,
    db: Session = Depends(get_db)
):
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    complaint = db.query(Complaint).filter(Complaint.id == fir.complaint_id).first()
    html_content = generate_fir_html_report(fir, complaint)
    return Response(content=html_content, media_type="text/html")
