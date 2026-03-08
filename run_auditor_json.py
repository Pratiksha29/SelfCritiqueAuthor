#!/usr/bin/env python3
"""
Modified auditor to save grievance reports as individual JSON files instead of CSV.
This prevents truncation issues with long text content.
"""

import json
import time
import argparse
from pathlib import Path
from typing import Tuple, Union

import pandas as pd

# Configuration
PROMPT_PATH = Path(__file__).parent / "auditor.prompt"
DATA_PATH = Path(__file__).parent / "ehr_messy.json"
OUTPUT_DIR = Path(__file__).parent / "grievance_reports"
API_DELAY_SEC = 2.0
MAX_RETRIES = 3

def get_client():
    """Initialize Gemini client."""
    import google.generativeai as genai
    
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment. "
                       "Get a key at: https://aistudio.google.com/apikey")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")

def load_auditor_prompt() -> str:
    with open(PROMPT_PATH, "r") as f:
        return f.read().strip()

def load_ehr_data() -> list:
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def parse_audit_response(response_text: str) -> Tuple[str, str]:
    """Parse auditor response. Returns (status, grievance)."""
    if not response_text or not response_text.strip():
        return "Not Consistent", "ERROR: Empty response"

    text = response_text.strip()
    upper = text.upper()

    if "STATUS: CONSISTENT" in upper:
        return "Consistent", "NA"

    if "STATUS: NOT CONSISTENT" in upper:
        status = "Not Consistent"
        idx = upper.find("STATUS: NOT CONSISTENT")
        after_status = text[idx + len("STATUS: NOT CONSISTENT"):].strip()
        grievance = after_status.lstrip("\n- ").strip()
        if not grievance:
            grievance = "Not Consistent (no details returned)"
        return status, grievance

    return "Not Consistent", f"Unparseable response: {text[:200]}..."

def audit_one_record(model, prompt_template: str, record: dict) -> Tuple[str, str]:
    """Audit a single record via Gemini."""
    record_json = json.dumps(record, indent=2)
    prompt = prompt_template.replace("{{MEDICAL_RECORD }}", record_json)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(
                prompt,
                generation_config={"temperature": 0.1, "max_output_tokens": 2048},
            )
            text = response.text if response.text else ""
            return parse_audit_response(text)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return "Not Consistent", f"ERROR: {str(e)}"
            print(f"  Retry {attempt + 1}/{MAX_RETRIES}...")
            time.sleep(RETRY_DELAY_SEC)
    
    return "Not Consistent", "ERROR: Max retries exceeded"

def save_grievance_as_json(record: dict, status: str, grievance: str, output_dir: Path):
    """Save individual grievance report as JSON file."""
    
    patient_id = record.get('Patient_ID', 'unknown')
    
    # Create grievance data structure
    grievance_data = {
        'patient_info': record,
        'audit_status': status,
        'grievance_report': grievance,
        'timestamp': time.time(),
        'full_report_preserved': True
    }
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Save individual JSON file
    file_path = output_dir / f"{patient_id}_grievance.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(grievance_data, f, indent=2, ensure_ascii=False)
    
    return file_path

def run_audits_with_json_output(
    json_path: Union[str, Path] = DATA_PATH,
    output_dir: Union[str, Path] = OUTPUT_DIR,
    demo_n: int = 0,
) -> Path:
    """Run audits and save each grievance as individual JSON file."""
    
    with open(json_path, "r") as f:
        records = json.load(f)

    if demo_n > 0:
        records = records[:demo_n]
        print(f"Demo mode: auditing first {len(records)} records only\n")

    prompt_template = load_auditor_prompt()
    model = get_client()
    total = len(records)
    
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    saved_files = []
    for i, rec in enumerate(records):
        print(f"Record {i + 1}/{total} (Patient_ID: {rec.get('Patient_ID', '?')})...")
        status, grievance = audit_one_record(model, prompt_template, rec)
        file_path = save_grievance_as_json(rec, status, grievance, output_dir)
        saved_files.append(file_path)
        if i < total - 1:
            time.sleep(API_DELAY_SEC)

    print("-" * 50)
    print(f"Done. Records: {total} | Grievance files saved: {len(saved_files)}")
    print(f"Output directory: {output_dir}")
    
    # Also create a summary CSV for quick reference
    summary_data = []
    for i, rec in enumerate(records):
        status, grievance = audit_one_record(model, prompt_template, rec)
        summary_data = {
            'Patient_ID': rec.get('Patient_ID'),
            'Name': rec.get('Name'),
            'Status': status,
            'Grievance_File': f"{rec.get('Patient_ID')}_grievance.json"
        }
        summary_data.append(summary_data)
    
    summary_df = pd.DataFrame(summary_data)
    summary_csv = output_dir / "grievance_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    
    print(f"Summary CSV: {summary_csv}")
    return output_dir

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", type=int, nargs="?", metavar="N", const=10, default=0, 
                       help="Run on first N records only")
    args = parser.parse_args()

    base = Path(__file__).parent
    run_audits_with_json_output(
        json_path=base / "ehr_messy.json",
        output_dir=base / "grievance_reports",
        demo_n=args.demo,
    )

if __name__ == "__main__":
    import os
    main()
