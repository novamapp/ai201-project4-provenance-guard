import uuid
import datetime
import os
import json
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS  # Added to allow the frontend to safely communicate with the backend

# signals
from stylometrics import analyze_text
from llm_signal import analyze_text_with_llm

app = Flask(__name__)
CORS(app)  # Enables cross-origin requests from frontend UI components

# Apply rate limits globally or directly per endpoint as needed. 
# Added a 10 requests/minute starter threshold for testing protection.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"],
    storage_uri="memory://",
)

# Shared Thread Pool for executing Async Detection Signals in parallel
executor = ThreadPoolExecutor(max_workers=4)
LOG_FILE_PATH = os.path.join(os.path.dirname(__file__), "audit_log.json")

# In-Memory Database (List) representing our operational audit log ecosystem
# AUDIT_LOGS = []


# ==========================================
# SIGNAL WORKERS (Parallel Execution)
# ==========================================

# def run_signal_1_llm(text, content_id, creator_id):
#     """
#     Signal 1: LLM Engine (llama-3.3-70b-versatile)
#     Measures: Semantic Clichés, rigid schemas, lack of intentional imperfections.
#     """
#     # TODO: Connect to Groq API client interface here.
#     # Placeholder baseline logic returns object containing both likelihood weights.
#     return {
#         "signal": 1,
#         "human_likely": 0.35,
#         "AI_likely": 0.65
#     }

# TODO: uncomment
def run_signal_1_llm(text, content_id, creator_id):
    """
    Signal 1: LLM Engine (llama-3.3-70b-versatile)
    Measures: Semantic Clichés, rigid schemas, lack of intentional imperfections.
    """
    try:
        # Execute the live call to the Groq API client
        metrics = analyze_text_with_llm(text)
        print('LLM Result:', metrics)
        
        return {
            "signal": 1,
            "human_likely": metrics["human_likely"],
            "AI_likely": metrics["AI_likely"]
        }
    except Exception as e:
        # Graceful fallback logging state to protect parallel thread execution pool
        app.logger.error(f"Error executing Signal 1 Pipeline on {content_id}: {str(e)}")
        return {
            "signal": 1,
            "human_likely": 0.5,
            "AI_likely": 0.5
        }


# def run_signal_2_stylometrics(text, content_id, creator_id):
#     """
#     Signal 2: Stylometric Heuristics (Custom Python Scripts)
#     Measures: Type-Token Ratio (TTR), punctuation density, line-length variance.
#     """
#     # TODO: Import and call your custom local analytical text processing functions.
#     return {
#         "signal": 2,
#         "human_likely": 0.20,
#         "AI_likely": 0.80
#     }

def run_signal_2_stylometrics(text, content_id, creator_id):
    """
    Signal 2: Stylometric Heuristics (Custom Python Scripts)
    Measures: Type-Token Ratio (TTR), punctuation density, line-length variance.
    """
    try:
        # Run the text through your custom analysis engine
        metrics = analyze_text(text)
        print('STYLOMETRICS Result:', metrics)
        
        return {
            "signal": 2,
            "human_likely": metrics["human_likely"],
            "AI_likely": metrics["AI_likely"]
        }
    except Exception as e:
        # Graceful fallback logging state to protect thread execution context
        app.logger.error(f"Error executing Signal 2 Pipeline on {content_id}: {str(e)}")
        return {
            "signal": 2,
            "human_likely": 0.5,
            "AI_likely": 0.5
        }


# ==========================================
# RUNTIME PIPELINE ENDPOINTS
# ==========================================

@app.route("/")
def home():
    return "Provenance Guard is running."

@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json() or {}
    text = data.get("text")
    creator_id = data.get("creator_id")
    
    if not text or not creator_id:
        return jsonify({"error": "Missing text or creator_id"}), 400

    content_id = str(uuid.uuid4())

    # Dispatch signals concurrently
    future_s1 = executor.submit(run_signal_1_llm, text, content_id, creator_id)
    future_s2 = executor.submit(run_signal_2_stylometrics, text, content_id, creator_id)

    s1_result = future_s1.result()
    s2_result = future_s2.result()

    # Matrix Aggregator logic
    # Trust Source 1 at 70%, Source 2 at 30%
    s1_weight, s2_weight = 0.7, 0.3

    # Use only the AI_likely metric (0 means 0% AI, 1 means 100% AI)
    s1_score = s1_result["AI_likely"]
    s2_score = s2_result["AI_likely"]

    # Calculate weighted average confidence
    confidence = round((s1_score * s1_weight) + (s2_score * s2_weight), 2)
    print(f"s1_result: {s1_result}, s1_score: {s1_score},confidence: {confidence}")

    if 0.0 <= confidence < 0.4:
        attribution = "likely_human"
        transparency_label = "It is highly likely that this work was created by a human."
    elif 0.4 <= confidence <= 0.7:
        attribution = "uncertain"
        transparency_label = "Source of work is uncertain."
    else:
        attribution = "likely_ai"
        transparency_label = "It is highly likely that this work was generated by AI."

    # Commit record directly into local audit_log.json file
    log_element = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "text": text,
        "creator_id": creator_id,
        "content_id": content_id,
        "confidence": confidence,
        "attribution": attribution,
        "appeals": []
    }
    
    current_logs = read_audit_logs()
    current_logs.append(log_element)
    write_audit_logs(current_logs)

    response_payload = {
        "content_id": content_id,
        "confidence": confidence,
        "attribution": attribution,
        "transparency_label": transparency_label
    }

    if attribution == "likely_ai":
        response_payload["offer_appeal"] = True

    return jsonify(response_payload), 200

@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json() or {}
    content_id = data.get("content_id")
    creator_reasoning = data.get("creator_reasoning")

    if not content_id or not creator_reasoning:
        return jsonify({"error": "Missing content_id or creator_reasoning"}), 400

    current_logs = read_audit_logs()
    target_record = next((log for log in current_logs if log["content_id"] == content_id), None)
    
    if not target_record:
        return jsonify({"error": "Record not found"}), 404

    if target_record["attribution"] != "likely_ai":
        return jsonify({"error": f"Cannot appeal current state: {target_record['attribution']}"}), 400

    # Mutate the status flag
    target_record["attribution"] = "under_review"
    
    appeal_event = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "creator_reasoning": creator_reasoning,
        "status": "pending",
        "reviewer_view_message": "Their appeal is pending."
    }
    target_record["appeals"].append(appeal_event)
    
    # Save back mutations to the file system
    write_audit_logs(current_logs)

    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Your appeal was received and is under review."
    }), 200

@app.route("/log", methods=["GET"])
def get_log():
    logs = read_audit_logs()
    return jsonify(logs[-1] if logs else {}), 200

# ==========================================
# TELEMETRY READ OPERATIONS
# ==========================================

# Helper utilities to handle JSON file CRUD operations securely
def read_audit_logs():
    if not os.path.exists(LOG_FILE_PATH):
        return []
    try:
        with open(LOG_FILE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []

def write_audit_logs(logs):
    try:
        with open(LOG_FILE_PATH, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        app.logger.error(f"Failed to write to file system: {str(e)}")


if __name__ == "__main__":
    app.run(port=8800, debug=True, use_reloader=False)