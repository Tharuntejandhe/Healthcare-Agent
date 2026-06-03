from typing import List, Dict, Any
from app.services.pdf_processor import extract_text_from_pdf
from app.services.ai.parser import parse_lab_report_lines
from app.services.ai.llm import get_llm
from langchain_core.prompts import PromptTemplate

def generate_health_summary(aggregated_data: List[Dict[str, Any]]) -> str:
    """
    Uses the LLM to generate a narrative summary of the patient's health 
    based on aggregated lab results.
    """
    if not aggregated_data:
        return "No medical data available to analyze."

    llm = get_llm()
    
    # Prepare data for LLM
    data_str = ""
    for item in aggregated_data:
        data_str += f"- {item['category']} | {item['test_name']}: {item['value']} {item['unit']} ({item['status']})\n"

    prompt_template = """You are a Senior Medical Analyst.
Review the following patient lab results and provide a concise, professional analytical report.

Data:
{data}

Structure:
1. Executive Summary: Overall health status.
2. Critical Findings: Highlight HIGH or LOW values and their potential implications.
3. Recommendations: Suggested follow-up tests or lifestyle adjustments.
4. Disclaimer: This is an AI-generated analysis.

Report:
"""
    prompt = PromptTemplate.from_template(prompt_template)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"data": data_str})
        return response.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def analyze_document(file_path: str) -> Dict[str, Any]:
    """
    Processes a single document and returns structured, categorized results.
    """
    # 1. Extract lines
    lines = extract_text_from_pdf(file_path)
    
    # 2. Parse and categorize
    structured_data = parse_lab_report_lines(lines)
    
    return {
        "source": file_path.split("/")[-1],
        "data": structured_data
    }

def get_analytical_report(file_paths: List[str]) -> Dict[str, Any]:
    """
    Generates a full analytical report for multiple documents.
    """
    all_results = []
    aggregated_data = []
    
    for path in file_paths:
        report = analyze_document(path)
        all_results.append(report)
        aggregated_data.extend(report["data"])
    
    # Generate LLM Summary
    summary = generate_health_summary(aggregated_data)
    
    # Calculate basic stats
    stats = {
        "total_tests": len(aggregated_data),
        "high_values": len([i for i in aggregated_data if i["status"] == "HIGH"]),
        "low_values": len([i for i in aggregated_data if i["status"] == "LOW"]),
        "normal_values": len([i for i in aggregated_data if i["status"] == "NORMAL"]),
    }
    
    return {
        "summary": summary,
        "stats": stats,
        "details_by_document": all_results,
        "aggregated_data": aggregated_data
    }
