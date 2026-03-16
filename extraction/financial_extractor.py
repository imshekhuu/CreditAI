
import re


def extract_financial_data(raw_text):
    financial_data = {
        "revenue": 0.0,
        "profit": 0.0,
        "debt": 0.0,
        "assets": 0.0,
        "liabilities": 0.0,
        "cashflow": 0.0
    }


    patterns = {
        "revenue": [
            r"(?:total\s+)?revenue[s]?\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"(?:total\s+)?sales\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"turnover\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"gross\s+income\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
        ],
        "profit": [
            r"net\s+profit\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"net\s+income\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"PAT\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"profit\s+after\s+tax\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"(?:total\s+)?profit\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
        ],
        "debt": [
            r"(?:total\s+)?debt\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"(?:total\s+)?borrowings?\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"(?:total\s+)?loans?\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
        ],
        "assets": [
            r"(?:total\s+)?assets?\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
        ],
        "liabilities": [
            r"(?:total\s+)?liabilit(?:y|ies)\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
        ],
        "cashflow": [
            r"(?:operating\s+)?cash\s*flow\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"net\s+cash\s*(?:flow)?\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
            r"cash\s+from\s+operations?\s*[:\-]?\s*[\₹\$]?\s*([\d,]+\.?\d*)",
        ],
    }

 
    for metric, regex_list in patterns.items():
        for pattern in regex_list:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                # Remove commas and convert to float
                value_str = match.group(1).replace(",", "")
                try:
                    financial_data[metric] = float(value_str)
                    print(f"[Extractor] Found {metric}: {financial_data[metric]}")
                except ValueError:
                    print(f"[Extractor] Could not parse value for {metric}: {value_str}")
                break  # Stop after first successful match for this metric

    return financial_data


def generate_demo_financial_data():

    demo_data = {
        "revenue": 145.0,
        "profit": 18.0,
        "debt": 70.0,
        "assets": 250.0,
        "liabilities": 120.0,
        "cashflow": 35.0
    }
    print("[Extractor] Using demo financial data.")
    return demo_data


def validate_financial_data(data):

    warnings = []

    # Check for zero or negative values
    for key, value in data.items():
        if value <= 0:
            warnings.append(f"{key.capitalize()} is zero or negative ({value}). This may indicate missing data.")

    # Basic sanity checks
    if data.get("debt", 0) > data.get("assets", 0) and data.get("assets", 0) > 0:
        warnings.append("Debt exceeds total assets — potential high-risk indicator.")

    if data.get("liabilities", 0) > data.get("assets", 0) and data.get("assets", 0) > 0:
        warnings.append("Liabilities exceed total assets — negative net worth detected.")

    if data.get("profit", 0) > data.get("revenue", 0) and data.get("revenue", 0) > 0:
        warnings.append("Reported profit exceeds revenue — possible data anomaly.")

    return {
        "valid": len(warnings) == 0,
        "warnings": warnings
    }
