import re
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Complaint, AIAnalysis
from app.schemas import (
    AIAnalysisIngestRequest, AIAnalysisResponse, ComplaintResponse
)
from app.utils.bnss_engine import log_timeline

router = APIRouter(prefix="/api/ai", tags=["Partner AI & NLP Model Integration"])

@router.get("/pending-complaints", response_model=List[ComplaintResponse])
def get_pending_complaints_for_ai(db: Session = Depends(get_db)):
    """
    Endpoint for Partner's AI Model / Background Worker:
    Returns complaints that have not been analyzed by AI yet.
    """
    analyzed_ids = [a.complaint_id for a in db.query(AIAnalysis.complaint_id).all()]
    pending = db.query(Complaint).filter(~Complaint.id.in_(analyzed_ids)).all() if analyzed_ids else db.query(Complaint).all()
    return pending

@router.post("/analyze-complaint", response_model=AIAnalysisResponse)
def ingest_partner_ai_analysis(
    payload: AIAnalysisIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint called by Partner's AI Model script to save predictions:
    NLP sections, NER entities, urgency, duplicate detection, and summary.
    """
    complaint = db.query(Complaint).filter(Complaint.id == payload.complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    existing_analysis = db.query(AIAnalysis).filter(AIAnalysis.complaint_id == payload.complaint_id).first()
    
    if existing_analysis:
        existing_analysis.recommended_sections = payload.recommended_sections
        existing_analysis.urgency_level = payload.urgency_level or "MEDIUM"
        existing_analysis.duplicate_risk_score = payload.duplicate_risk_score or 0.0
        existing_analysis.duplicate_candidate_ids = payload.duplicate_candidate_ids or []
        existing_analysis.extracted_entities = payload.extracted_entities or {}
        existing_analysis.complaint_summary = payload.complaint_summary
        existing_analysis.sentiment_emotion = payload.sentiment_emotion
        analysis = existing_analysis
    else:
        analysis = AIAnalysis(
            complaint_id=payload.complaint_id,
            recommended_sections=payload.recommended_sections,
            urgency_level=payload.urgency_level or "MEDIUM",
            duplicate_risk_score=payload.duplicate_risk_score or 0.0,
            duplicate_candidate_ids=payload.duplicate_candidate_ids or [],
            extracted_entities=payload.extracted_entities or {},
            complaint_summary=payload.complaint_summary,
            sentiment_emotion=payload.sentiment_emotion
        )
        db.add(analysis)

    db.commit()
    db.refresh(analysis)

    # Log in timeline
    log_timeline(
        db=db,
        complaint_id=complaint.id,
        title="AI Case Triage & NLP Assessment Completed",
        description=f"AI engine completed analysis: Urgency [{analysis.urgency_level}], Duplicate Risk [{analysis.duplicate_risk_score}%]. Legal sections identified.",
        event_type="ai_assessment",
        actor_name="SMART-FIR-360-AI-ENGINE"
    )

    return analysis

@router.post("/mock-analyze/{complaint_id}", response_model=AIAnalysisResponse)
def mock_run_ai_analysis(complaint_id: int, db: Session = Depends(get_db)):
    """
    Built-in smart heuristic analyzer for live hackathon presentation & fallback:
    Extracts entities, matches Bharatiya Nyaya Sanhita (BNS) sections,
    and calculates duplicate risk score based on existing records.
    """
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    text = f"{complaint.title} {complaint.description} {complaint.category}".lower()

    # Rule-based NLP section matcher for Indian BNS 2023
    recommended_sections = []
    urgency = "MEDIUM"

    if any(k in text for k in ["theft", "stolen", "snatched", "pickpocket", "robbed", "burglary"]):
        recommended_sections.append({
            "section": "BNS Section 303(2)",
            "title": "Punishment for Theft",
            "confidence": 0.94,
            "cognizable": True,
            "bailable": False
        })
        if "snatched" in text or "robbed" in text:
            recommended_sections.append({
                "section": "BNS Section 309",
                "title": "Robbery / Snatching",
                "confidence": 0.88,
                "cognizable": True,
                "bailable": False
            })
            urgency = "HIGH"

    if any(k in text for k in ["cyber", "online", "otp", "phishing", "fraud", "hacked", "bank account", "scam"]):
        recommended_sections.append({
            "section": "BNS Section 318(4)",
            "title": "Cheating and dishonestly inducing delivery of property",
            "confidence": 0.96,
            "cognizable": True,
            "bailable": False
        })
        recommended_sections.append({
            "section": "IT Act Section 66D",
            "title": "Cheating by personation by using computer resource",
            "confidence": 0.91,
            "cognizable": True,
            "bailable": False
        })

    if any(k in text for k in ["assault", "beat", "hit", "injury", "weapon", "knife", "blood", "attack"]):
        recommended_sections.append({
            "section": "BNS Section 115(2)",
            "title": "Voluntarily causing hurt",
            "confidence": 0.92,
            "cognizable": True,
            "bailable": True
        })
        urgency = "HIGH"

    if any(k in text for k in ["threat", "kill", "extort", "ransom", "acid", "murder"]):
        urgency = "CRITICAL"
        recommended_sections.append({
            "section": "BNS Section 351(2)",
            "title": "Criminal Intimidation",
            "confidence": 0.89,
            "cognizable": True,
            "bailable": False
        })

    if not recommended_sections:
        recommended_sections.append({
            "section": "BNS Section 316",
            "title": "Criminal Breach of Trust / General Offence",
            "confidence": 0.75,
            "cognizable": True,
            "bailable": True
        })

    # Entity extraction regex
    amounts = re.findall(r"(?:rs\.?|inr|₹)\s?(\d+(?:,\d+)*(?:\.\d+)?)", text)
    phone_numbers = re.findall(r"\b(?:\+91[-\s]?)?[6789]\d{9}\b", complaint.description)
    
    extracted_entities = {
        "financial_loss": f"₹{amounts[0]}" if amounts else "Not specified",
        "phone_numbers_detected": phone_numbers if phone_numbers else [],
        "key_location": complaint.location_name,
        "suspect_mentions": [w.strip() for w in (complaint.accused_details or "").split(",") if w.strip()]
    }

    # Duplicate detection heuristic: check other complaints in same station or category
    other_complaints = db.query(Complaint).filter(
        Complaint.id != complaint.id,
        Complaint.police_station == complaint.police_station
    ).limit(10).all()

    duplicate_candidates = []
    max_similarity = 12.0
    for oc in other_complaints:
        # Check text overlap
        words_a = set(complaint.title.lower().split())
        words_b = set(oc.title.lower().split())
        overlap = len(words_a.intersection(words_b))
        if overlap >= 2:
            duplicate_candidates.append(oc.complaint_number)
            max_similarity = max(max_similarity, 78.5)

    summary = (
        f"NLP Analysis: Complaint pertains to {complaint.category} reported at {complaint.location_name}. "
        f"Key elements indicate potential offence under {recommended_sections[0]['section']}. "
        f"Priority classification: {urgency}."
    )

    req = AIAnalysisIngestRequest(
        complaint_id=complaint_id,
        recommended_sections=recommended_sections,
        urgency_level=urgency,
        duplicate_risk_score=max_similarity,
        duplicate_candidate_ids=duplicate_candidates,
        extracted_entities=extracted_entities,
        complaint_summary=summary,
        sentiment_emotion="Aggrieved / High Distress" if urgency in ["HIGH", "CRITICAL"] else "Neutral Statement"
    )

    return ingest_partner_ai_analysis(req, db)
