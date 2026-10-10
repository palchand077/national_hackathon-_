import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, engine, Base
from app.models import User, Complaint, FIR, Evidence, TimelineEvent, AIAnalysis, UserRole, ComplaintStatus, FIRStatus
from app.auth import hash_password

def seed():
    print("Initializing Database schema...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding Users (Citizens & Police Personnel)...")
        # 1. Users
        police1 = User(
            email="inspector.sharma@police.gov.in",
            password_hash=hash_password("Police@123"),
            full_name="Inspector Rajesh Sharma",
            phone="+91 9811223344",
            role=UserRole.POLICE_OFFICER.value,
            badge_number="DL-CP-4402",
            police_station="Connaught Place PS, New Delhi"
        )
        police2 = User(
            email="si.priya@police.gov.in",
            password_hash=hash_password("Police@123"),
            full_name="SI Priya Nair",
            phone="+91 9822334455",
            role=UserRole.POLICE_OFFICER.value,
            badge_number="DL-CYB-1092",
            police_station="Cyber Crime Unit, Delhi"
        )
        citizen1 = User(
            email="rohit.verma@example.com",
            password_hash=hash_password("Citizen@123"),
            full_name="Rohit Verma",
            phone="+91 9876543210",
            aadhar_last4="8472",
            role=UserRole.CITIZEN.value
        )
        citizen2 = User(
            email="ananya.sen@example.com",
            password_hash=hash_password("Citizen@123"),
            full_name="Ananya Sen",
            phone="+91 9123456780",
            aadhar_last4="3921",
            role=UserRole.CITIZEN.value
        )
        citizen3 = User(
            email="vikram.singh@example.com",
            password_hash=hash_password("Citizen@123"),
            full_name="Vikram Singh",
            phone="+91 9988776655",
            aadhar_last4="5109",
            role=UserRole.CITIZEN.value
        )

        db.add_all([police1, police2, citizen1, citizen2, citizen3])
        db.commit()

        print("Seeding Complaints, FIRs, Timeline and Evidence under BNSS 173...")
        now = datetime.utcnow()

        # Case 1: Theft -> Registered FIR
        c1 = Complaint(
            complaint_number="COMP-2026-0001",
            citizen_id=citizen1.id,
            title="Theft of Laptop Bag containing Dell XPS and Documents",
            category="Theft & Burglary",
            description="While waiting near Rajiv Chowk Metro Gate No. 3, two unidentified men on a black Pulsar motorcycle snatched my black backpack containing a Dell XPS 15 laptop (Serial: DLX-9941), original Aadhar card, and wallet containing Rs. 4,500 cash.",
            incident_date=(now - timedelta(days=2)).strftime("%Y-%m-%d"),
            incident_time="18:30",
            location_name="Rajiv Chowk Metro Gate 3, Connaught Place",
            latitude=28.6328,
            longitude=77.2197,
            police_station="Connaught Place PS, New Delhi",
            accused_details="Two men, black motorcycle, helmet on, approximately 25-30 years of age.",
            witness_details="Tea stall vendor near gate 3 witnessed the escape direction towards Barakhamba Road.",
            status=ComplaintStatus.FIR_REGISTERED.value,
            is_e_complaint=True,
            verification_deadline=now - timedelta(days=1),
            verified_at=now - timedelta(days=2)
        )
        db.add(c1)
        db.commit()

        # FIR for Case 1
        fir1 = FIR(
            fir_number="FIR/DLCP/2026/0001",
            complaint_id=c1.id,
            police_station="Connaught Place PS, New Delhi",
            investigating_officer_id=police1.id,
            bns_sections="BNS Section 303(2) [Theft], BNS Section 304(2) [Snatching]",
            acts_and_sections="Bharatiya Nyaya Sanhita, 2023 (BNS)",
            date_of_occurrence=(now - timedelta(days=2)).strftime("%d-%b-%Y"),
            date_reported=now - timedelta(days=2),
            place_of_occurrence="Near Gate 3, Rajiv Chowk, New Delhi",
            complainant_name=citizen1.full_name,
            accused_details=c1.accused_details,
            investigation_summary="CCTV footage from Metro Security requisitioned. Suspect registration plate trace initiated under Section 173 BNSS.",
            status=FIRStatus.UNDER_INVESTIGATION.value
        )
        db.add(fir1)
        db.commit()

        # Timeline for Case 1
        tl1_1 = TimelineEvent(
            complaint_id=c1.id,
            title="Electronic Complaint Submitted",
            description="Complaint filed via SMART FIR 360 portal under BNSS Section 173(1).",
            event_type="bnss_action",
            actor_name=citizen1.full_name,
            created_at=now - timedelta(days=2, hours=4)
        )
        tl1_2 = TimelineEvent(
            complaint_id=c1.id,
            title="Aadhaar OTP e-Verification Complete",
            description="Complainant authenticated digital identity within the statutory 3-day verification window.",
            event_type="bnss_action",
            actor_name=citizen1.full_name,
            created_at=now - timedelta(days=2, hours=3)
        )
        tl1_3 = TimelineEvent(
            complaint_id=c1.id,
            fir_id=fir1.id,
            title="FIR Registered & IO Assigned",
            description="FIR/DLCP/2026/0001 registered under BNS 303(2)/304(2). IO Inspector Rajesh Sharma assigned.",
            event_type="fir_generated",
            actor_name=police1.full_name,
            created_at=now - timedelta(days=2)
        )
        db.add_all([tl1_1, tl1_2, tl1_3])

        # AI Analysis for Case 1
        ai1 = AIAnalysis(
            complaint_id=c1.id,
            recommended_sections=[
                {"section": "BNS Section 304(2)", "title": "Snatching", "confidence": 0.96, "cognizable": True, "bailable": False},
                {"section": "BNS Section 303(2)", "title": "Theft", "confidence": 0.94, "cognizable": True, "bailable": False}
            ],
            urgency_level="HIGH",
            duplicate_risk_score=15.0,
            duplicate_candidate_ids=[],
            extracted_entities={
                "stolen_items": ["Dell XPS 15 laptop", "Aadhar card", "Wallet with Rs. 4,500"],
                "vehicle": "Black Pulsar Motorcycle",
                "escape_route": "Barakhamba Road",
                "suspect_count": 2
            },
            complaint_summary="Snatching incident involving two suspects on a motorcycle at Rajiv Chowk Metro Gate 3. Laptop and documents stolen. High urgency due to active serial snatcher pattern in central district.",
            sentiment_emotion="Aggrieved / Urgent"
        )
        db.add(ai1)

        # Case 2: Cyber Fraud -> Preliminary Inquiry (BNSS 173(3))
        c2 = Complaint(
            complaint_number="COMP-2026-0002",
            citizen_id=citizen2.id,
            title="Phishing Scam & Unauthorized UPI Withdrawals amounting to Rs. 85,000",
            category="Cybercrime & Online Fraud",
            description="Received an SMS posing as electricity bill disconnection notice with an APK link. After clicking, my phone was remotely accessed and three unauthorized transactions of Rs. 25,000, Rs. 35,000 and Rs. 25,000 were debited to UPI ID fastpay99@ybl.",
            incident_date=(now - timedelta(days=1)).strftime("%Y-%m-%d"),
            incident_time="11:15",
            location_name="Sector 62, Electronic City, Noida",
            latitude=28.6280,
            longitude=77.3649,
            police_station="Cyber Crime Unit, Delhi",
            accused_details="Beneficiary UPI ID: fastpay99@ybl, Phone sender: +91 9711002288",
            witness_details="Bank transaction SMS logs and mobile screenshot attached.",
            status=ComplaintStatus.PRELIMINARY_INQUIRY.value,
            is_e_complaint=True,
            verification_deadline=now + timedelta(days=2),
            verified_at=now - timedelta(days=1),
            inquiry_deadline=now + timedelta(days=13),
            inquiry_notes="DySP permission reference: DYSP/CYBER/2026/041. Notice dispatched to beneficiary bank under Sec 94 BNSS to freeze fraudulent account."
        )
        db.add(c2)
        db.commit()

        tl2_1 = TimelineEvent(
            complaint_id=c2.id,
            title="Electronic Complaint Filed",
            description="Lodged via Citizen e-Portal for cyber financial fraud.",
            event_type="bnss_action",
            actor_name=citizen2.full_name,
            created_at=now - timedelta(days=1)
        )
        tl2_2 = TimelineEvent(
            complaint_id=c2.id,
            title="Preliminary Inquiry Initiated under BNSS Sec 173(3)",
            description="Preliminary inquiry ordered (14-day statutory period). Bank account freeze request sent to nodal officer.",
            event_type="bnss_action",
            actor_name=police2.full_name,
            created_at=now - timedelta(hours=18)
        )
        db.add_all([tl2_1, tl2_2])

        ai2 = AIAnalysis(
            complaint_id=c2.id,
            recommended_sections=[
                {"section": "BNS Section 318(4)", "title": "Cheating & Inducing Delivery of Property", "confidence": 0.98, "cognizable": True, "bailable": False},
                {"section": "IT Act Section 66D", "title": "Cheating by Personation using Computer", "confidence": 0.95, "cognizable": True, "bailable": False}
            ],
            urgency_level="CRITICAL",
            duplicate_risk_score=82.5,
            duplicate_candidate_ids=["COMP-2026-0004"],
            extracted_entities={
                "financial_loss": "₹85,000",
                "target_upi": "fastpay99@ybl",
                "phone_numbers_detected": ["+91 9711002288"],
                "modus_operandi": "Electricity bill disconnection APK trojan"
            },
            complaint_summary="Critical financial fraud: Remote APK malware drained ₹85,000 via 3 transactions. High probability match with organized phishing syndicate operating in NCR.",
            sentiment_emotion="Severe Distress / Fraud"
        )
        db.add(ai2)

        # Case 3: Vehicle Theft -> Verified, Ready for FIR
        c3 = Complaint(
            complaint_number="COMP-2026-0003",
            citizen_id=citizen3.id,
            title="Motorcycle Stolen from Parking Area outside Market",
            category="Theft & Burglary",
            description="My Royal Enfield Classic 350 (Registration: DL-4C-NA-8812, Black color) parked in front of Main Market Complex was found missing at 9:00 PM.",
            incident_date=now.strftime("%Y-%m-%d"),
            incident_time="20:00",
            location_name="Main Market, South Extension Part II",
            latitude=28.5684,
            longitude=77.2215,
            police_station="Connaught Place PS, New Delhi",
            accused_details="Unknown suspects. Parking attendant reports 2 men loitering near vehicle.",
            status=ComplaintStatus.VERIFIED.value,
            is_e_complaint=True,
            verification_deadline=now + timedelta(days=3),
            verified_at=now
        )
        db.add(c3)
        db.commit()

        tl3_1 = TimelineEvent(
            complaint_id=c3.id,
            title="e-Complaint Filed & Verified",
            description="Complainant e-verified via DigiLocker token. Ready for FIR registration or IO allocation.",
            event_type="bnss_action",
            actor_name=citizen3.full_name,
            created_at=now
        )
        db.add(tl3_1)

        ai3 = AIAnalysis(
            complaint_id=c3.id,
            recommended_sections=[
                {"section": "BNS Section 303(2)", "title": "Punishment for Theft", "confidence": 0.95, "cognizable": True, "bailable": False}
            ],
            urgency_level="MEDIUM",
            duplicate_risk_score=22.0,
            duplicate_candidate_ids=[],
            extracted_entities={
                "vehicle_registration": "DL-4C-NA-8812",
                "vehicle_model": "Royal Enfield Classic 350",
                "stolen_items": ["Royal Enfield Classic 350"]
            },
            complaint_summary="Motor vehicle theft reported at South Extension Market. AI cross-referenced registration plate DL-4C-NA-8812 against active automated toll alerts.",
            sentiment_emotion="Aggrieved"
        )
        db.add(ai3)

        # Case 4: Recent e-Complaint submitted (Pending 3-day verification)
        c4 = Complaint(
            complaint_number="COMP-2026-0004",
            citizen_id=citizen1.id,
            title="Attempted Online Fraud via Fake Job Portal",
            category="Cybercrime & Online Fraud",
            description="Received an email asking for security deposit of Rs. 12,000 for a remote data entry job. Suspected fraudulent organization posing as government recruitment.",
            incident_date=now.strftime("%Y-%m-%d"),
            incident_time="14:00",
            location_name="Barakhamba Road, Connaught Place",
            latitude=28.6295,
            longitude=77.2280,
            police_station="Cyber Crime Unit, Delhi",
            accused_details="Email: hr@recruitment-central-portal.net",
            status=ComplaintStatus.SUBMITTED.value,
            is_e_complaint=True,
            verification_deadline=now + timedelta(days=3)
        )
        db.add(c4)
        db.commit()

        tl4_1 = TimelineEvent(
            complaint_id=c4.id,
            title="Electronic Complaint Lodged",
            description="Submitted online under BNSS Section 173(1). Complainant has 3 days to verify signature.",
            event_type="bnss_action",
            actor_name=citizen1.full_name,
            created_at=now
        )
        db.add(tl4_1)

        db.commit()
        print("Database successfully seeded with realistic cases aligned with BNSS Section 173!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed()
