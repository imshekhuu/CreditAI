import json
from datetime import datetime


def generate_report(company_info, financial_data, risk_result, llm_reasoning):


    revenue = financial_data.get("revenue", 0)
    profit = financial_data.get("profit", 0)
    debt = financial_data.get("debt", 0)
    assets = financial_data.get("assets", 0)
    liabilities = financial_data.get("liabilities", 0)
    cashflow = financial_data.get("cashflow", 0)

    ratios = {
        "profit_margin": round((profit / revenue * 100), 2) if revenue > 0 else 0,
        "debt_to_asset": round((debt / assets * 100), 2) if assets > 0 else 0,
        "debt_to_equity": round((debt / max(assets - liabilities, 1) * 100), 2),
        "current_ratio": round((assets / max(liabilities, 1)), 2),
        "return_on_assets": round((profit / max(assets, 1) * 100), 2),
    }


    health_score = _calculate_health_score(financial_data, risk_result, ratios)


    report = {
        "report_metadata": {
            "report_id": f"CUR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "report_type": "Credit Underwriting Analysis",
            "version": "1.0",
            "analyst": "AI Credit Underwriting System"
        },
        "company_overview": {
            "company_name": company_info.get("company_name", "N/A"),
            "sector": company_info.get("sector", "N/A"),
            "loan_amount": company_info.get("loan_amount", "N/A"),
            "loan_purpose": company_info.get("loan_purpose", "N/A"),
            "company_age": company_info.get("company_age", "N/A"),
        },
        "financial_summary": {
            "metrics": financial_data,
            "ratios": ratios,
            "health_score": health_score,
        },
        "risk_assessment": {
            "risk_level": risk_result.get("risk_level", "N/A"),
            "risk_probability": risk_result.get("risk_probability", 0),
            "confidence": risk_result.get("confidence", 0),
            "model_accuracy": risk_result.get("model_accuracy", 0),
            "feature_importance": risk_result.get("feature_importance", {}),
            "all_probabilities": risk_result.get("all_probabilities", {}),
        },
        "ai_analysis": {
            "financial_summary": llm_reasoning.get("financial_summary", ""),
            "risk_explanation": llm_reasoning.get("risk_explanation", ""),
            "swot_analysis": llm_reasoning.get("swot_analysis", ""),
            "loan_recommendation": llm_reasoning.get("loan_recommendation", ""),
            "source": llm_reasoning.get("source", "simulated"),
        },
        "final_recommendation": {
            "decision": llm_reasoning.get("recommendation_status", _determine_decision(risk_result)),
            "risk_level": risk_result.get("risk_level", "N/A"),
            "health_score": health_score,
            "summary": _generate_executive_summary(company_info, financial_data, risk_result),
        }
    }

    print(f"[Report] Generated report: {report['report_metadata']['report_id']}")
    return report


def _calculate_health_score(financial_data, risk_result, ratios):

    score = 50  


    pm = ratios.get("profit_margin", 0)
    if pm > 15:
        score += 25
    elif pm > 10:
        score += 18
    elif pm > 5:
        score += 10
    elif pm > 0:
        score += 5
    else:
        score -= 10

    # Debt management (max +25)
    dta = ratios.get("debt_to_asset", 0)
    if dta < 25:
        score += 25
    elif dta < 40:
        score += 18
    elif dta < 60:
        score += 8
    else:
        score -= 10

    # Risk level (max +30 for low, 0 for high)
    risk_level = risk_result.get("risk_level", "Medium")
    if risk_level == "Low":
        score += 15
    elif risk_level == "Medium":
        score += 0
    else:
        score -= 20

    # Cash flow (max +20)
    cashflow = financial_data.get("cashflow", 0)
    if cashflow > 30:
        score += 10
    elif cashflow > 10:
        score += 5
    elif cashflow > 0:
        score += 2
    else:
        score -= 5

    # Clamp to 0-100
    return max(0, min(100, score))


def _determine_decision(risk_result):
    """Determine loan decision based on risk level."""
    risk_level = risk_result.get("risk_level", "Medium")
    if risk_level == "Low":
        return "APPROVE"
    elif risk_level == "Medium":
        return "CONDITIONAL APPROVE"
    else:
        return "REJECT"


def _generate_executive_summary(company_info, financial_data, risk_result):
    """Generate a brief executive summary for the report."""
    company_name = company_info.get("company_name", "The applicant")
    risk_level = risk_result.get("risk_level", "Medium")
    loan_amount = company_info.get("loan_amount", "N/A")

    return (
        f"{company_name} has applied for a loan of ₹{loan_amount} Cr. "
        f"Based on analysis of financial statements and ML risk modeling, "
        f"the entity is classified as {risk_level} Risk. "
        f"Revenue stands at ₹{financial_data.get('revenue', 0)} Cr with a net profit of "
        f"₹{financial_data.get('profit', 0)} Cr and total debt of ₹{financial_data.get('debt', 0)} Cr."
    )
