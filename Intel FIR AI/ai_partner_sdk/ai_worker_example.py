"""
=============================================================================
SMART FIR 360 - AI/ML Partner Integration Client
=============================================================================
This script illustrates how the AI / NLP developer on your team can connect
their custom machine learning model (e.g. HuggingFace, RoBERTa, Gemini, LLaMA)
directly to the SMART FIR 360 platform via REST API.

API Contract:
1. GET  /api/ai/pending-complaints  -> List of unanalyzed complaints
2. POST /api/ai/analyze-complaint   -> Ingest NLP/ML predictions & legal sections
=============================================================================
"""

import json
import time
import urllib.request
import urllib.error

BACKEND_BASE_URL = "http://localhost:8000"

def fetch_pending_complaints():
    """Poll the SMART FIR 360 backend for cases needing AI processing."""
    url = f"{BACKEND_BASE_URL}/api/ai/pending-complaints"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SMART-FIR-AI-Worker/1.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"Connection error to backend: {e}")
        return []

def run_ai_partner_inference(complaint_text: str, category: str):
    """
    >>> YOUR AI/ML TEAM ADAPTS THIS FUNCTION <<<
    Plug your model inference code here (e.g., PyTorch, Hugging Face transformers,
    legal NER model, sentence similarity for duplicate detection).
    """
    print(f"  [AI Model] Running NLP inference on text: {complaint_text[:60]}...")
    
    # Example simulated ML prediction structure
    # Match against Bharatiya Nyaya Sanhita (BNS) 2023 provisions
    mock_prediction = {
        "recommended_sections": [
            {
                "section": "BNS Section 303(2)",
                "title": "Punishment for Theft",
                "confidence": 0.95,
                "cognizable": True,
                "bailable": False
            }
        ],
        "urgency_level": "HIGH",
        "duplicate_risk_score": 14.5,
        "duplicate_candidate_ids": [],
        "extracted_entities": {
            "modus_operandi": "Drive-by snatching",
            "detected_keywords": ["stolen", "phone", "motorcycle"]
        },
        "complaint_summary": "Automated NLP summary: Informant reports theft of mobile device by motorbike riders.",
        "sentiment_emotion": "Distressed / High urgency"
    }
    return mock_prediction

def post_ai_results_to_smart_fir(complaint_id: int, ai_output: dict):
    """Send predictions back to SMART FIR 360 platform."""
    url = f"{BACKEND_BASE_URL}/api/ai/analyze-complaint"
    payload = {
        "complaint_id": complaint_id,
        "recommended_sections": ai_output.get("recommended_sections", []),
        "urgency_level": ai_output.get("urgency_level", "MEDIUM"),
        "duplicate_risk_score": ai_output.get("duplicate_risk_score", 0.0),
        "duplicate_candidate_ids": ai_output.get("duplicate_candidate_ids", []),
        "extracted_entities": ai_output.get("extracted_entities", {}),
        "complaint_summary": ai_output.get("complaint_summary", ""),
        "sentiment_emotion": ai_output.get("sentiment_emotion", "Neutral")
    }
    
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "SMART-FIR-AI-Worker/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            result = json.loads(res.read().decode("utf-8"))
            print(f"  [Success] AI Analysis successfully ingested for Case ID: {complaint_id}")
            return result
    except urllib.error.HTTPError as e:
        print(f"  [Failed] Backend returned status {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"  [Error] {e}")
        return None

def main():
    print("==================================================")
    print("  SMART FIR 360 - AI Partner Integration Worker  ")
    print("==================================================")
    print("Polling SMART FIR 360 backend for pending complaints...\n")

    pending_list = fetch_pending_complaints()
    print(f"Found {len(pending_list)} complaint(s) awaiting AI analysis.")

    for item in pending_list:
        c_id = item["id"]
        c_num = item["complaint_number"]
        full_text = f"{item['title']} - {item['description']}"
        category = item["category"]

        print(f"\nProcessing Complaint: {c_num} (ID: {c_id})")
        # Run custom AI model
        ai_result = run_ai_partner_inference(full_text, category)
        
        # Post back to SMART FIR 360
        post_ai_results_to_smart_fir(c_id, ai_result)
        time.sleep(0.5)

    print("\nWorker batch finished. Integration complete!")

if __name__ == "__main__":
    main()
