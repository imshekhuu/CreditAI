import os
from dotenv import load_dotenv

load_dotenv()

# ---- Configuration ----
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")  # or llama3, phi3, gemma2, etc.
HF_MODEL = os.getenv("HF_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")


def _build_prompt(company_info, financial_data, risk_result):

    prompt = f"""You are a senior credit analyst at a leading financial institution.
Generate a comprehensive credit underwriting analysis based on the following data.

=== COMPANY INFORMATION ===
Company Name: {company_info.get('company_name', 'N/A')}
Sector/Industry: {company_info.get('sector', 'N/A')}
Loan Amount Requested: {company_info.get('loan_amount', 'N/A')} Cr
Loan Purpose: {company_info.get('loan_purpose', 'Business Expansion')}
Company Age: {company_info.get('company_age', 'N/A')} years

=== FINANCIAL DATA (in Crores) ===
Revenue: ₹{financial_data.get('revenue', 0)} Cr
Net Profit: ₹{financial_data.get('profit', 0)} Cr
Total Debt: ₹{financial_data.get('debt', 0)} Cr
Total Assets: ₹{financial_data.get('assets', 0)} Cr
Total Liabilities: ₹{financial_data.get('liabilities', 0)} Cr
Cash Flow: ₹{financial_data.get('cashflow', 0)} Cr

=== ML MODEL RISK ASSESSMENT ===
Risk Level: {risk_result.get('risk_level', 'N/A')}
Risk Confidence: {risk_result.get('confidence', 0)}%
Model Accuracy: {risk_result.get('model_accuracy', 0)}%

=== REQUIRED OUTPUT ===
Please provide:

1. FINANCIAL SUMMARY: Overview of the company's financial health with key ratios.
2. RISK EXPLANATION: Why the ML model assigned this risk level, key risk factors.
3. SWOT ANALYSIS: Strengths, Weaknesses, Opportunities, Threats (at least 2 each).
4. LOAN RECOMMENDATION: Approve / Conditional Approve / Reject with reasons.

Be specific, data-driven, and professional."""

    return prompt



def generate_credit_reasoning(company_info, financial_data, risk_result):

    prompt = _build_prompt(company_info, financial_data, risk_result)

 
    result = _try_ollama(prompt)
    if result:
        return result


    result = _try_huggingface(prompt)
    if result:
        return result

    print("[LLM Engine] No LLM provider available. Using simulated analysis.")
    return _generate_simulated_response(company_info, financial_data, risk_result)



def _try_ollama(prompt):

    try:
        from langchain_community.llms import Ollama

        print(f"[LLM Engine] Trying Ollama with model '{OLLAMA_MODEL}'...")

        llm = Ollama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.7,
        )

        
        response = llm.invoke(prompt)

        if response and len(response.strip()) > 50:
            print(f"[LLM Engine] ✅ Ollama ({OLLAMA_MODEL}) generated analysis successfully.")
            return _parse_llm_response(response, source=f"ollama/{OLLAMA_MODEL}")
        else:
            print("[LLM Engine] Ollama returned empty or too-short response.")
            return None

    except ImportError:
        print("[LLM Engine] langchain-community not installed. Skipping Ollama.")
        return None
    except Exception as e:
        print(f"[LLM Engine] Ollama not available: {str(e)}")
        return None



def _try_huggingface(prompt):

    if not HUGGINGFACE_TOKEN:
        print("[LLM Engine] No HUGGINGFACEHUB_API_TOKEN set. Skipping HuggingFace.")
        return None

    try:
        from langchain_huggingface import HuggingFaceEndpoint

        print(f"[LLM Engine] Trying HuggingFace Hub with model '{HF_MODEL}'...")

        llm = HuggingFaceEndpoint(
            repo_id=HF_MODEL,
            huggingfacehub_api_token=HUGGINGFACE_TOKEN,
            temperature=0.7,
            max_new_tokens=1500,
        )

        response = llm.invoke(prompt)

        if response and len(response.strip()) > 50:
            print(f"[LLM Engine] ✅ HuggingFace ({HF_MODEL}) generated analysis successfully.")
            return _parse_llm_response(response, source=f"huggingface/{HF_MODEL}")
        else:
            print("[LLM Engine] HuggingFace returned empty or too-short response.")
            return None

    except ImportError:
        print("[LLM Engine] langchain-huggingface not installed. Skipping HuggingFace.")
        return None
    except Exception as e:
        print(f"[LLM Engine] HuggingFace Hub failed: {str(e)}")
        return None



def _parse_llm_response(raw_text, source="unknown"):
    text = raw_text.strip()

    
    sections = {
        "financial_summary": "",
        "risk_explanation": "",
        "swot_analysis": "",
        "loan_recommendation": "",
    }

  
    import re

   
    patterns = [
        
        (r"(?:1\.?\s*)?(?:\*\*)?FINANCIAL\s+SUMMARY(?:\*\*)?[:\s]*", "financial_summary"),
        (r"(?:2\.?\s*)?(?:\*\*)?RISK\s+EXPLANATION(?:\*\*)?[:\s]*", "risk_explanation"),
        (r"(?:3\.?\s*)?(?:\*\*)?SWOT\s+ANALYSIS(?:\*\*)?[:\s]*", "swot_analysis"),
        (r"(?:4\.?\s*)?(?:\*\*)?LOAN\s+RECOMMENDATION(?:\*\*)?[:\s]*", "loan_recommendation"),
    ]

    
    positions = []
    for pattern, key in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            positions.append((match.start(), match.end(), key))

    if len(positions) >= 2:
        
        positions.sort(key=lambda x: x[0])

        for i, (start, end, key) in enumerate(positions):
            if i + 1 < len(positions):
                sections[key] = text[end:positions[i + 1][0]].strip()
            else:
                sections[key] = text[end:].strip()

        print(f"[LLM Engine] Successfully parsed {len(positions)} sections from LLM response.")
    else:
       
        sections["financial_summary"] = text
        print("[LLM Engine] Could not parse sections. Using full response as financial summary.")

 
    recommendation_status = "CONDITIONAL APPROVE"
    lower_text = text.lower()
    if "reject" in lower_text and "recommend" in lower_text:
        recommendation_status = "REJECT"
    elif "approve" in lower_text and "conditional" not in lower_text:
        recommendation_status = "APPROVE"

    sections["source"] = source
    sections["raw_response"] = text
    sections["recommendation_status"] = recommendation_status

    return sections



def _generate_simulated_response(company_info, financial_data, risk_result):
    company_name = company_info.get("company_name", "the applicant company")
    sector = company_info.get("sector", "Financial Services")
    loan_amount = company_info.get("loan_amount", "N/A")
    revenue = financial_data.get("revenue", 0)
    profit = financial_data.get("profit", 0)
    debt = financial_data.get("debt", 0)
    assets = financial_data.get("assets", 0)
    liabilities = financial_data.get("liabilities", 0)
    cashflow = financial_data.get("cashflow", 0)
    risk_level = risk_result.get("risk_level", "Medium")
    confidence = risk_result.get("confidence", 75)

    # Calculate financial ratios
    profit_margin = (profit / revenue * 100) if revenue > 0 else 0
    debt_to_asset = (debt / assets * 100) if assets > 0 else 0
    debt_to_equity = (debt / (assets - liabilities) * 100) if (assets - liabilities) > 0 else 0

    # Determine recommendation based on risk level
    if risk_level == "Low":
        recommendation = "APPROVE"
        rec_detail = (
            f"Based on our comprehensive analysis, we recommend **APPROVAL** of the ₹{loan_amount} Cr loan "
            f"for {company_name}. The company demonstrates strong financial health with a healthy profit "
            f"margin of {profit_margin:.1f}% and manageable debt levels. The debt-to-asset ratio of "
            f"{debt_to_asset:.1f}% is well within acceptable limits.\n\n"
            f"**Conditions:**\n"
            f"- Standard quarterly financial reporting requirements\n"
            f"- Maintain debt-to-equity ratio below 2.0x\n"
            f"- Annual review of credit facility\n"
            f"- Recommended interest rate: Base rate + 1.5-2.0%"
        )
    elif risk_level == "Medium":
        recommendation = "CONDITIONAL APPROVE"
        rec_detail = (
            f"We recommend **CONDITIONAL APPROVAL** of the ₹{loan_amount} Cr loan for {company_name}. "
            f"While the company shows decent fundamentals, there are areas of concern that require "
            f"risk mitigation measures.\n\n"
            f"**Conditions:**\n"
            f"- Collateral coverage of at least 1.5x loan amount\n"
            f"- Monthly financial reporting for the first year\n"
            f"- Debt-to-equity covenant not to exceed 3.0x\n"
            f"- Personal guarantee from promoters\n"
            f"- Loan disbursement in tranches tied to milestones\n"
            f"- Recommended interest rate: Base rate + 3.0-4.0%"
        )
    else:
        recommendation = "REJECT"
        rec_detail = (
            f"Based on our analysis, we recommend **REJECTION** of the ₹{loan_amount} Cr loan request "
            f"from {company_name}. The company's financial profile presents significant credit risks "
            f"that cannot be adequately mitigated.\n\n"
            f"**Key Concerns:**\n"
            f"- High debt-to-asset ratio of {debt_to_asset:.1f}%\n"
            f"- Insufficient profit margins ({profit_margin:.1f}%) to service additional debt\n"
            f"- Weak cash flow position relative to proposed loan amount\n\n"
            f"**Alternative Suggestions:**\n"
            f"- Consider a smaller loan amount with stronger collateral\n"
            f"- Re-apply after improving debt-to-equity ratio\n"
            f"- Explore equity funding as an alternative"
        )

    # Build the full analysis
    analysis = {
        "financial_summary": (
            f"### Financial Health Overview — {company_name}\n\n"
            f"{company_name} operates in the **{sector}** sector and has requested a loan of "
            f"**₹{loan_amount} Cr**.\n\n"
            f"**Key Financial Metrics:**\n"
            f"| Metric | Value | Assessment |\n"
            f"|--------|-------|------------|\n"
            f"| Revenue | ₹{revenue} Cr | {'Strong' if revenue > 100 else 'Moderate' if revenue > 50 else 'Weak'} |\n"
            f"| Net Profit | ₹{profit} Cr | {'Healthy' if profit > 15 else 'Adequate' if profit > 5 else 'Concerning'} |\n"
            f"| Total Debt | ₹{debt} Cr | {'Manageable' if debt < 50 else 'Moderate' if debt < 100 else 'High'} |\n"
            f"| Total Assets | ₹{assets} Cr | {'Strong base' if assets > 200 else 'Moderate base'} |\n"
            f"| Cash Flow | ₹{cashflow} Cr | {'Positive' if cashflow > 0 else 'Negative'} |\n\n"
            f"**Key Ratios:**\n"
            f"- Profit Margin: **{profit_margin:.1f}%** {'✅' if profit_margin > 10 else '⚠️' if profit_margin > 5 else '❌'}\n"
            f"- Debt-to-Asset Ratio: **{debt_to_asset:.1f}%** {'✅' if debt_to_asset < 40 else '⚠️' if debt_to_asset < 60 else '❌'}\n"
            f"- Debt-to-Equity Ratio: **{debt_to_equity:.1f}%** {'✅' if debt_to_equity < 100 else '⚠️' if debt_to_equity < 200 else '❌'}"
        ),
        "risk_explanation": (
            f"### Risk Assessment Analysis\n\n"
            f"The ML credit scoring model has classified {company_name} as **{risk_level} Risk** "
            f"with a confidence of **{confidence}%**.\n\n"
            f"**Risk Factors Analyzed:**\n\n"
            f"1. **Revenue Stability**: "
            f"{'The company shows strong revenue generation, suggesting a stable business model and market position.' if revenue > 100 else 'Moderate revenue levels indicate room for growth but possible market dependency risks.' if revenue > 50 else 'Low revenue raises concerns about business viability and ability to service debt obligations.'}\n\n"
            f"2. **Profitability**: "
            f"{'Healthy profit margins indicate efficient operations and strong pricing power.' if profit > 15 else 'Adequate profitability, though margins could be improved for better debt servicing capacity.' if profit > 5 else 'Low or negative profitability is a significant concern for loan repayment capacity.'}\n\n"
            f"3. **Debt Burden**: "
            f"{'Current debt levels are manageable relative to the company size and earning capacity.' if debt < 50 else 'Moderate debt levels require careful monitoring, especially if additional borrowing is being considered.' if debt < 100 else 'High existing debt is a major risk factor. Additional borrowing significantly increases default probability.'}\n\n"
            f"4. **Cash Flow Health**: "
            f"{'Positive cash flow provides a comfortable buffer for loan servicing.' if cashflow > 20 else 'Cash flow is positive but may be tight for additional debt obligations.' if cashflow > 0 else 'Negative or zero cash flow is a critical concern for debt servicing.'}"
        ),
        "swot_analysis": (
            f"### SWOT Analysis — {company_name}\n\n"
            f"**💪 Strengths:**\n"
            f"- {'Strong revenue base of ₹' + str(revenue) + ' Cr provides solid foundation' if revenue > 100 else 'Established presence in the ' + sector + ' sector'}\n"
            f"- {'Healthy profit margins demonstrate operational efficiency' if profit > 10 else 'Positive profitability despite challenging market conditions'}\n"
            f"- {'Strong asset base of ₹' + str(assets) + ' Cr provides collateral value' if assets > 200 else 'Diversified asset portfolio provides stability'}\n\n"
            f"**⚠️ Weaknesses:**\n"
            f"- {'Debt levels of ₹' + str(debt) + ' Cr require careful management' if debt > 50 else 'Limited scale compared to larger industry peers'}\n"
            f"- {'Profit margin of ' + str(round(profit_margin, 1)) + '% could be improved' if profit_margin < 15 else 'Dependency on core revenue streams'}\n"
            f"- {'Cash flow constraints may limit operational flexibility' if cashflow < 30 else 'Working capital management needs optimization'}\n\n"
            f"**🚀 Opportunities:**\n"
            f"- Market expansion in the {sector} sector with growing demand\n"
            f"- Digital transformation initiatives could improve operational efficiency\n"
            f"- Strategic partnerships could diversify revenue streams\n\n"
            f"**🔴 Threats:**\n"
            f"- Regulatory changes in the {sector} sector could impact operations\n"
            f"- Economic slowdown could affect revenue growth and debt servicing\n"
            f"- Increasing competition from fintech and digital-first players"
        ),
        "loan_recommendation": (
            f"### Final Loan Recommendation\n\n"
            f"**Decision: {recommendation}**\n\n"
            f"{rec_detail}"
        ),
        "source": "simulated (no LLM configured)",
        "recommendation_status": recommendation
    }

    print(f"[LLM Engine] Generated simulated analysis: {recommendation}")
    return analysis
