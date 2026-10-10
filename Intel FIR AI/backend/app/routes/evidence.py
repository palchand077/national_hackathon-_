import hashlib
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Evidence, Complaint, User
from app.schemas import EvidenceResponse
from app.auth import get_current_user
from app.config import UPLOAD_DIR
from app.utils.bnss_engine import log_timeline

router = APIRouter(prefix="/api/evidence", tags=["Evidence Locker & Digital Custody"])

@router.post("/upload/{complaint_id}", response_model=EvidenceResponse)
async def upload_evidence(
    complaint_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form("Uploaded digital evidence"),
    file_type: Optional[str] = Form("document"), # image, video, audio, document
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Read bytes and compute SHA256 integrity hash
    contents = await file.read()
    sha256_hash = hashlib.sha256(contents).hexdigest()
    file_size_kb = max(1, len(contents) // 1024)

    # Safe file path
    safe_filename = f"{complaint_id}_{sha256_hash[:10]}_{file.filename.replace(' ', '_')}"
    target_path = UPLOAD_DIR / safe_filename
    with open(target_path, "wb") as f:
        f.write(contents)

    # Determine type if not passed
    ext = Path(file.filename).suffix.lower()
    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        file_type = "image"
    elif ext in [".mp4", ".mov", ".mkv", ".avi"]:
        file_type = "video"
    elif ext in [".mp3", ".wav", ".m4a", ".aac"]:
        file_type = "audio"
    else:
        file_type = "document"

    evidence = Evidence(
        complaint_id=complaint.id,
        fir_id=complaint.fir.id if complaint.fir else None,
        file_name=file.filename,
        file_path=str(target_path),
        file_type=file_type,
        file_size_kb=file_size_kb,
        description=description,
        hash_sha256=sha256_hash,
        uploaded_by_id=current_user.id
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    # Log in timeline
    log_timeline(
        db=db,
        complaint_id=complaint.id,
        fir_id=complaint.fir.id if complaint.fir else None,
        title=f"Evidence Deposited: {file.filename}",
        description=f"Evidence file ({file_type}, {file_size_kb} KB) registered with digital custody hash: SHA-256[{sha256_hash[:16]}...]",
        event_type="evidence_added",
        actor_name=current_user.full_name
    )

    return evidence

@router.get("/{complaint_id}", response_model=List[EvidenceResponse])
def get_complaint_evidences(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return db.query(Evidence).filter(Evidence.complaint_id == complaint_id).all()

@router.get("/file/{evidence_id}")
def download_evidence(
    evidence_id: int,
    db: Session = Depends(get_db)
):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence or not Path(evidence.file_path).exists():
        raise HTTPException(status_code=404, detail="Evidence file not found")

    return FileResponse(evidence.file_path, filename=evidence.file_name)
