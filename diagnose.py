
print("Checking imports...")
try:
    import flask
    print("Flask ok")
    import pdfplumber
    print("pdfplumber ok")
    import pandas
    print("pandas ok")
    import sklearn
    print("sklearn ok")
    import langchain
    print("langchain ok")
    import dotenv
    print("dotenv ok")
    
    print("\nChecking project modules...")
    from document_processing.pdf_reader import extract_text_from_pdf
    print("pdf_reader ok")
    from extraction.financial_extractor import extract_financial_data
    print("extractor ok")
    from models.risk_model import predict_risk
    print("risk_model ok (trained)")
    from llm.reasoning_engine import generate_credit_reasoning
    print("reasoning_engine ok")
    from reports.report_generator import generate_report
    print("report_generator ok")
    
    print("\nStarting diagnostic server...")
    from app import app
    print("App imported ok")
except Exception as e:
    import traceback
    traceback.print_exc()
