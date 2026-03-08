#!/usr/bin/env python3
"""
Enhanced auditor that saves grievance reports directly to JSON files.
This completely bypasses CSV truncation issues.
"""

import json
import time
import os
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
        # For demo purposes, create mock client
        print("⚠️  No API key found - using demo mode")
        return None
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

def create_demo_grievance(record: dict) -> Tuple[str, str]:
    """Create realistic demo grievance for testing without API."""
    
    # Generate realistic grievances based on common EHR issues
    patient_id = record.get('Patient_ID', 'UNKNOWN')
    name = record.get('Name', 'Unknown')
    age = record.get('Age', 0)
    dob = record.get('Date_of_Birth', 'Unknown')
    
    grievances = []
    
    # Check for common issues
    if name and any(c.islower() for c in name) or any(c.isupper() for c in name):
        grievances.append(f"Name capitalization inconsistency: '{name}' does not follow professional formatting standards")
    
    if age and dob and '19' in dob:
        try:
            birth_year = int(dob.split('/')[-1])
            expected_age = 2026 - birth_year
            if abs(age - expected_age) > 1:
                grievances.append(f"Age-DOB mismatch: Stated age {age} does not align with DOB {dob} (expected ~{expected_age})")
        except:
            pass
    
    # Add more realistic issues
    if len(grievances) == 0:
        grievances.append("Data formatting inconsistency detected in patient record")
    
    # Create CoVE format grievance
    total_inconsistencies = len(grievances)
    cove_process = "\n".join([f"{i+1}. {g}" for i, g in enumerate(grievances)])
    
    full_grievance = f"""TOTAL INCONSISTENCIES FOUND: {total_inconsistencies}

CHAIN OF VERIFICATION (CoVE) PROCESS:
{cove_process}

CORRECTION NEEDED:
- Standardize name formatting according to professional medical record standards
- Verify age calculation against date of birth
- Ensure all demographic fields follow consistent data entry protocols
- Cross-reference with original source documents for accuracy"""
    
    return "Not Consistent", full_grievance

def audit_one_record(model, prompt_template: str, record: dict) -> Tuple[str, str]:
    """Audit a single record via Gemini or demo mode."""
    
    if model is None:
        # Demo mode - create realistic grievance
        return create_demo_grievance(record)
    
    # Real API mode
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

def save_grievance_json(record: dict, status: str, grievance: str, output_dir: Path):
    """Save grievance as complete JSON file."""
    
    patient_id = record.get('Patient_ID', 'unknown')
    
    # Create comprehensive grievance data
    grievance_data = {
        'patient_info': record,
        'audit_results': {
            'status': status,
            'grievance_report': grievance,
            'report_length': len(grievance),
            'full_text_preserved': True,
            'timestamp': time.time()
        },
        'metadata': {
            'auditor_version': '2.0',
            'output_format': 'json',
            'truncation_prevented': True
        }
    }
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Save JSON file
    file_path = output_dir / f"{patient_id}_complete_grievance.json"
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(grievance_data, f, indent=2, ensure_ascii=False)
    
    return file_path

def run_auditor_json_only(
    json_path: Union[str, Path] = DATA_PATH,
    output_dir: Union[str, Path] = OUTPUT_DIR,
    demo_n: int = 0,
) -> Path:
    """Run auditor and save directly to JSON files (no CSV)."""
    
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
    grievance_lengths = []
    
    for i, rec in enumerate(records):
        print(f"Record {i + 1}/{total} (Patient_ID: {rec.get('Patient_ID', '?')})...")
        status, grievance = audit_one_record(model, prompt_template, rec)
        file_path = save_grievance_json(rec, status, grievance, output_dir)
        saved_files.append(file_path)
        grievance_lengths.append(len(grievance))
        
        print(f"   📄 Grievance length: {len(grievance)} characters")
        print(f"   ✅ Saved: {file_path.name}")
        
        if i < total - 1:
            time.sleep(API_DELAY_SEC)

    print("-" * 60)
    print(f"🎉 Auditor JSON output complete!")
    print(f"📊 Total records: {total}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📄 Files created: {len(saved_files)}")
    print(f"📏 Average grievance length: {sum(grievance_lengths)/len(grievance_lengths):.0f} chars")
    
    # Create summary
    summary = {
        'audit_summary': {
            'total_records': total,
            'files_created': [f.name for f in saved_files],
            'output_directory': str(output_dir),
            'grievance_stats': {
                'average_length': sum(grievance_lengths)/len(grievance_lengths) if grievance_lengths else 0,
                'min_length': min(grievance_lengths) if grievance_lengths else 0,
                'max_length': max(grievance_lengths) if grievance_lengths else 0
            }
        }
    }
    
    summary_path = output_dir / "audit_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"📋 Summary: {summary_path}")
    return output_dir

def main():
    parser = argparse.ArgumentParser(description="EHR Auditor - JSON Output (No CSV Truncation)")
    parser.add_argument("--demo", type=int, nargs="?", metavar="N", const=10, default=0,
                       help="Run on first N records only")
    parser.add_argument("--output", type=str, default="grievance_reports",
                       help="Output directory for grievance JSON files")
    args = parser.parse_args()

    base = Path(__file__).parent
    run_auditor_json_only(
        json_path=base / "ehr_messy.json",
        output_dir=base / args.output,
        demo_n=args.demo,
    )

if __name__ == "__main__":
    main()
