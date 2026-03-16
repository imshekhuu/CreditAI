import os
import json
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ----- Import project modules -----
from document_processing.pdf_reader import extract_text_from_pdf
from extraction.financial_extractor import (
    extract_financial_data,
    generate_demo_financial_data,
    validate_financial_data,
)
from models.risk_model import predict_risk
from llm.reasoning_engine import generate_credit_reasoning
from reports.report_generator import generate_report

# ----- Flask App Configuration -----
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "credit-underwriting-secret-key-2024")

@app.before_request
def log_request_info():
    print(f"[Request] {request.method} {request.path}")

# Upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB max upload

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ----- In-memory session store (simple, single-user demo) -----
# In production, use Redis/DB-backed sessions.
_session_store = {
    "company_info": {},
    "uploaded_file": None,
    "raw_text": "",
    "financial_data": {},
    "risk_result": {},
    "llm_reasoning": {},
    "report": {},
}


def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Render the main dashboard page."""
    return render_template("index.html")


@app.route("/health")
def health():
    return jsonify({"status": "up", "port": 5050})


@app.route("/upload", methods=["POST"])
def upload_pdf():
    """
    Handle PDF file upload and company information form submission.
    """
    try:
        
        company_info = {
            "company_name": request.form.get("company_name", "Unknown Company"),
            "sector": request.form.get("sector", "General"),
            "loan_amount": request.form.get("loan_amount", "0"),
            "loan_purpose": request.form.get("loan_purpose", "Business Expansion"),
            "company_age": request.form.get("company_age", "0"),
        }
        _session_store["company_info"] = company_info
        print(f"[App] Company info received: {company_info['company_name']}")

        
        if "pdf_file" not in request.files:
            
            print("[App] No PDF file uploaded. Will use demo financial data.")
            _session_store["uploaded_file"] = None
            _session_store["raw_text"] = ""
            return jsonify({
                "status": "success",
                "message": "Company information saved. No PDF uploaded — demo data will be used.",
                "company_info": company_info,
                "pdf_uploaded": False,
            })

        file = request.files["pdf_file"]

        if file.filename == "":
            _session_store["uploaded_file"] = None
            _session_store["raw_text"] = ""
            return jsonify({
                "status": "success",
                "message": "Company information saved. No PDF selected — demo data will be used.",
                "company_info": company_info,
                "pdf_uploaded": False,
            })

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            _session_store["uploaded_file"] = filepath

            
            raw_text = extract_text_from_pdf(filepath)
            _session_store["raw_text"] = raw_text

            print(f"[App] PDF uploaded and text extracted: {filename}")

            return jsonify({
                "status": "success",
                "message": f"PDF '{filename}' uploaded and processed successfully.",
                "company_info": company_info,
                "pdf_uploaded": True,
                "text_preview": raw_text[:500] + "..." if len(raw_text) > 500 else raw_text,
                "text_length": len(raw_text),
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Invalid file type. Please upload a PDF file.",
            }), 400

    except Exception as e:
        print(f"[App Error] Upload failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Upload failed: {str(e)}",
        }), 500



@app.route("/extract", methods=["POST"])
def extract_data():
    """
    Extract financial metrics from the uploaded PDF text.
    """
    try:
        raw_text = _session_store.get("raw_text", "")

        if raw_text and not raw_text.startswith("[PDF Reader"):
           
            financial_data = extract_financial_data(raw_text)
            print("[App] Extracted financial data from PDF text.")
        else:
            
            financial_data = generate_demo_financial_data()
            print("[App] Using demo financial data (no valid PDF text).")

        validation = validate_financial_data(financial_data)

        _session_store["financial_data"] = financial_data

        return jsonify({
            "status": "success",
            "financial_data": financial_data,
            "validation": validation,
            "source": "pdf" if raw_text and not raw_text.startswith("[PDF Reader") else "demo",
        })

    except Exception as e:
        print(f"[App Error] Extraction failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Data extraction failed: {str(e)}",
        }), 500



@app.route("/predict", methods=["POST"])
def predict():
    """
    Run the ML credit risk model on extracted financial data.
    """
    try:
        financial_data = _session_store.get("financial_data", {})

        if not financial_data:
            return jsonify({
                "status": "error",
                "message": "No financial data available. Please extract data first.",
            }), 400

        # Run prediction
        risk_result = predict_risk(financial_data)
        _session_store["risk_result"] = risk_result

        print(f"[App] Risk prediction: {risk_result['risk_level']} ({risk_result['confidence']}%)")

        return jsonify({
            "status": "success",
            "risk_result": risk_result,
        })

    except Exception as e:
        print(f"[App Error] Prediction failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Risk prediction failed: {str(e)}",
        }), 500


# ===================================================================
#  ROUTE: Generate LLM Reasoning
# ===================================================================
@app.route("/reason", methods=["POST"])
def reason():
    """
    Generate AI-powered credit underwriting reasoning using LLM.
    """
    try:
        company_info = _session_store.get("company_info", {})
        financial_data = _session_store.get("financial_data", {})
        risk_result = _session_store.get("risk_result", {})

        if not financial_data or not risk_result:
            return jsonify({
                "status": "error",
                "message": "Missing data. Please complete extraction and prediction first.",
            }), 400

        # Generate LLM reasoning
        llm_reasoning = generate_credit_reasoning(company_info, financial_data, risk_result)
        _session_store["llm_reasoning"] = llm_reasoning

        print(f"[App] LLM reasoning generated (source: {llm_reasoning.get('source', 'unknown')})")

        return jsonify({
            "status": "success",
            "reasoning": llm_reasoning,
        })

    except Exception as e:
        print(f"[App Error] Reasoning failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"AI reasoning generation failed: {str(e)}",
        }), 500



@app.route("/report", methods=["POST"])
def generate_final_report():
    """
    Generate the complete credit underwriting report.
    """
    try:
        company_info = _session_store.get("company_info", {})
        financial_data = _session_store.get("financial_data", {})
        risk_result = _session_store.get("risk_result", {})
        llm_reasoning = _session_store.get("llm_reasoning", {})

        if not all([company_info, financial_data, risk_result, llm_reasoning]):
            return jsonify({
                "status": "error",
                "message": "Incomplete analysis. Please complete all previous steps.",
            }), 400

        # Generate the report
        report = generate_report(company_info, financial_data, risk_result, llm_reasoning)
        _session_store["report"] = report

        return jsonify({
            "status": "success",
            "report": report,
        })

    except Exception as e:
        print(f"[App Error] Report generation failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Report generation failed: {str(e)}",
        }), 500



if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AI Credit Underwriting System")
    print("  Starting Flask server...")
    print("  Open: http://localhost:5050")
    print("=" * 60 + "\n")

    app.run(debug=True, host="0.0.0.0", port=7860, use_reloader=False)