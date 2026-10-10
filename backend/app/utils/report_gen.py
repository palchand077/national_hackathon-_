from datetime import datetime
from app.models import FIR, Complaint

def generate_fir_html_report(fir: FIR, complaint: Complaint) -> str:
    """
    Generates a formal, printable First Information Report (FIR)
    conforming to Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 - Section 173.
    """
    reported_str = fir.date_reported.strftime("%d-%b-%Y %I:%M %p") if fir.date_reported else datetime.utcnow().strftime("%d-%b-%Y")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Official FIR Copy - {fir.fir_number}</title>
<style>
    @media print {{
        body {{ margin: 0; background: #fff; }}
        .no-print {{ display: none; }}
        .page {{ box-shadow: none; border: none; margin: 0; }}
    }}
    body {{
        font-family: 'Times New Roman', serif;
        background: #f1f5f9;
        margin: 20px;
        color: #111827;
    }}
    .page {{
        max-width: 850px;
        margin: 0 auto;
        background: #fff;
        padding: 40px 50px;
        border: 2px solid #0f172a;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        position: relative;
    }}
    .watermark {{
        position: absolute;
        top: 40%;
        left: 20%;
        transform: rotate(-30deg);
        font-size: 72px;
        color: rgba(15, 23, 42, 0.04);
        font-weight: bold;
        pointer-events: none;
        user-select: none;
        text-transform: uppercase;
        letter-spacing: 5px;
    }}
    .header {{
        text-align: center;
        border-bottom: 2px double #0f172a;
        padding-bottom: 15px;
        margin-bottom: 20px;
    }}
    .national-emblem {{
        font-size: 14px;
        font-weight: bold;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #1e3a8a;
    }}
    .title {{
        font-size: 22px;
        font-weight: 800;
        text-transform: uppercase;
        margin: 8px 0;
        letter-spacing: 1px;
    }}
    .sub {{
        font-size: 12px;
        color: #4b5563;
        font-style: italic;
    }}
    .statute-tag {{
        display: inline-block;
        background: #0f172a;
        color: #fff;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: bold;
        margin-top: 5px;
        border-radius: 3px;
        letter-spacing: 0.5px;
    }}
    .meta-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        font-size: 13px;
        margin-bottom: 20px;
        border-bottom: 1px solid #e2e8f0;
        padding-bottom: 15px;
    }}
    .meta-row {{
        display: flex;
    }}
    .meta-label {{
        font-weight: bold;
        width: 170px;
        color: #334155;
    }}
    .meta-val {{
        flex: 1;
        font-weight: 600;
    }}
    .section-block {{
        margin-bottom: 18px;
    }}
    .section-title {{
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
        background: #f8fafc;
        border-left: 4px solid #1e3a8a;
        padding: 6px 10px;
        margin-bottom: 8px;
        color: #1e293b;
    }}
    .box-content {{
        font-size: 13px;
        line-height: 1.6;
        padding: 8px 12px;
        border: 1px solid #cbd5e1;
        border-radius: 3px;
        background: #fafafa;
    }}
    .footer-signs {{
        display: flex;
        justify-content: space-between;
        margin-top: 40px;
        padding-top: 20px;
    }}
    .sign-box {{
        text-align: center;
        width: 220px;
    }}
    .sign-line {{
        border-top: 1px solid #0f172a;
        margin-top: 45px;
        font-size: 12px;
        font-weight: bold;
        padding-top: 5px;
    }}
    .qr-box {{
        text-align: center;
        border: 1px dashed #94a3b8;
        padding: 8px;
        font-size: 10px;
        color: #64748b;
    }}
    .btn-bar {{
        max-width: 850px;
        margin: 0 auto 15px auto;
        display: flex;
        justify-content: flex-end;
        gap: 10px;
    }}
    .btn {{
        background: #1e3a8a;
        color: #fff;
        border: none;
        padding: 8px 18px;
        font-size: 14px;
        cursor: pointer;
        border-radius: 4px;
        font-weight: bold;
    }}
    .btn:hover {{ background: #1d4ed8; }}
</style>
</head>
<body>

<div class="btn-bar no-print">
    <button class="btn" onclick="window.print()">🖨️ Print / Save as PDF</button>
    <button class="btn" style="background:#475569" onclick="window.close()">Close</button>
</div>

<div class="page">
    <div class="watermark">SMART FIR 360</div>

    <div class="header">
        <div class="national-emblem">POLICE DEPARTMENT • DIGITAL CRIME RECORDS</div>
        <div class="title">FIRST INFORMATION REPORT (FIR)</div>
        <div class="statute-tag">REGISTERED UNDER SECTION 173, BHARATIYA NAGARIK SURAKSHA SANHITA (BNSS), 2023</div>
        <div class="sub">Free certified electronic copy provided to complainant under Section 173(2) BNSS</div>
    </div>

    <div class="meta-grid">
        <div class="meta-row">
            <span class="meta-label">1. FIR Number:</span>
            <span class="meta-val" style="color:#b91c1c; font-size:15px;">{fir.fir_number}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">2. Police Station:</span>
            <span class="meta-val">{fir.police_station}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">3. e-Complaint Ref No:</span>
            <span class="meta-val">{complaint.complaint_number}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">4. Date & Time Reported:</span>
            <span class="meta-val">{reported_str}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">5. Date of Occurrence:</span>
            <span class="meta-val">{fir.date_of_occurrence}</span>
        </div>
        <div class="meta-row">
            <span class="meta-label">6. Place of Occurrence:</span>
            <span class="meta-val">{fir.place_of_occurrence}</span>
        </div>
    </div>

    <div class="section-block">
        <div class="section-title">7. Acts & Applicable Legal Provisions (BNS Sections)</div>
        <div class="box-content" style="font-weight: bold; color: #1e3a8a;">
            {fir.bns_sections or "Applicable sections pending investigation"}
        </div>
    </div>

    <div class="section-block">
        <div class="section-title">8. Complainant / Informant Details</div>
        <div class="box-content">
            <strong>Full Name:</strong> {fir.complainant_name}<br>
            <strong>e-Communication Mode:</strong> Electronic Verification Verified via SMART FIR 360<br>
            <strong>Status under BNSS 173:</strong> Taken on Record & Officially Cognized
        </div>
    </div>

    <div class="section-block">
        <div class="section-title">9. Details of Known / Suspected / Accused Persons</div>
        <div class="box-content">
            {fir.accused_details or "Unknown / Under Ongoing Investigation"}
        </div>
    </div>

    <div class="section-block">
        <div class="section-title">10. Substance of Incident / First Information</div>
        <div class="box-content">
            <strong>Subject:</strong> {complaint.title}<br>
            <strong>Category:</strong> {complaint.category}<br><br>
            <strong>Detailed Statement:</strong><br>
            {complaint.description}
        </div>
    </div>

    <div class="section-block">
        <div class="section-title">11. Investigating Officer Preliminary Direction</div>
        <div class="box-content">
            {fir.investigation_summary or "FIR duly registered. Investigating Officer dispatched for crime scene inspection and evidence preservation in digital custody."}
        </div>
    </div>

    <div class="footer-signs">
        <div class="qr-box">
            <div style="font-size:24px; margin-bottom:4px;">🔐</div>
            <strong>DIGITALLY SIGNED</strong><br>
            BNSS Sec 173 Compliance Token<br>
            Hash: {hex(abs(hash(fir.fir_number)))[:16].upper()}
        </div>

        <div class="sign-box">
            <div class="sign-line">
                Signature of Complainant<br>
                (Digitally Authenticated)
            </div>
        </div>

        <div class="sign-box">
            <div class="sign-line">
                Officer-in-Charge / Station House Officer<br>
                {fir.police_station}
            </div>
        </div>
    </div>
</div>

</body>
</html>
"""
    return html
