"""
EHR Auditor: Uses auditor.prompt and Gemini API to find inconsistencies in EHR data.
Processes each record separately and outputs audit_report.csv with two extra columns:
  - Consistent_or_Not: "Consistent" | "Not Consistent"
  - Grievance_Report: "NA" when consistent, else the grievance text.

Requires GEMINI_API_KEY or GOOGLE_API_KEY environment variable.

Usage:
  python run_auditor.py           # Audit all records (one API call per record)
  python run_auditor.py --demo    # Quick test with first N records
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Tuple, Union

import pandas as pd

# Load auditor prompt
PROMPT_PATH = Path(__file__).parent / "auditor.prompt"
DATA_PATH = Path(__file__).parent / "ehr_messy.json"
OUTPUT_CSV = Path(__file__).parent / "audit_report.csv"
# Delay between API calls (seconds) to reduce rate-limit errors
API_DELAY_SEC = 2.0
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5


def get_client():
    """Initialize Gemini client."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    try:
        import google.generativeai as genai
    except ImportError:
        print("Installing google-generativeai...")
        os.system(f"{sys.executable} -m pip install google-generativeai -q")
        import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print(
            "Error: Set GEMINI_API_KEY or GOOGLE_API_KEY in your environment.\n"
            "Get a key at: https://aistudio.google.com/apikey"
        )
        sys.exit(1)
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def load_auditor_prompt() -> str:
    with open(PROMPT_PATH, "r") as f:
        return f.read().strip()


def load_ehr_data() -> list:
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def parse_audit_response(response_text: str) -> Tuple[str, str]:
    """
    Parse auditor response. Returns (status, grievance).
    status: "Consistent" or "Not Consistent"
    grievance: "NA" if consistent, else the grievance report text.
    """
    if not response_text or not response_text.strip():
        return "Not Consistent", "ERROR: Empty response"

    text = response_text.strip()
    upper = text.upper()

    if "STATUS: CONSISTENT" in upper:
        status = "Consistent"
        grievance = "NA"
        return status, grievance

    if "STATUS: NOT CONSISTENT" in upper:
        status = "Not Consistent"
        # Grievance = everything after the status line (optional: after "Grievance Report" / "Grievance:")
        idx = upper.find("STATUS: NOT CONSISTENT")
        after_status = text[idx + len("STATUS: NOT CONSISTENT") :].strip()
        # Remove leading newlines/dashes; take rest as grievance
        # Keep original formatting for full grievance report
        grievance = after_status.lstrip("\n- ").strip()
        if not grievance:
            grievance = "Not Consistent (no details returned)"
        return status, grievance

    # Unclear response
    return "Not Consistent", f"Unparseable response: {text[:200]}..."


def audit_one_record(model, prompt_template: str, record: dict) -> Tuple[str, str]:
    """Audit a single record via Gemini. Returns (status, grievance)."""
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
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower():
                if attempt < MAX_RETRIES - 1:
                    print(f"  Rate limited; waiting {RETRY_DELAY_SEC}s before retry...")
                    time.sleep(RETRY_DELAY_SEC)
                    continue
            return "Not Consistent", f"ERROR: {err_str[:500]}"
    return "Not Consistent", "ERROR: Max retries exceeded"


def run_audits(
    json_path: Union[str, Path] = DATA_PATH,
    output_csv: Union[str, Path] = OUTPUT_CSV,
    demo_n: int = 0,
) -> Path:
    """
    Run auditor on each record in the JSON file; write audit_report CSV.
    Returns path to output CSV.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    with open(json_path, "r") as f:
        records = json.load(f)

    if demo_n > 0:
        records = records[:demo_n]
        print(f"Demo mode: auditing first {len(records)} records only\n")

    prompt_template = load_auditor_prompt()
    model = get_client()
    total = len(records)
    rows = []
    for i, rec in enumerate(records):
        print(f"Record {i + 1}/{total} (Patient_ID: {rec.get('Patient_ID', '?')})...")
        status, grievance = audit_one_record(model, prompt_template, rec)
        row = dict(rec)
        row["Consistent_or_Not"] = status
        row["Grievance_Report"] = grievance
        rows.append(row)
        if i < total - 1:
            time.sleep(API_DELAY_SEC)

    df = pd.DataFrame(rows)
    out = Path(output_csv)
    
    # Write CSV with proper handling for long text content
    df.to_csv(out, index=False, encoding="utf-8", 
              quoting=csv.QUOTE_ALL,  # Quote all fields to preserve long text
              quotechar='"', 
              escapechar='\\',  # Proper escaping
              lineterminator='\n')
    inconsistent_count = sum(1 for r in rows if r["Consistent_or_Not"] == "Not Consistent")
    print("-" * 50)
    print(f"Done. Records: {total} | Not Consistent: {inconsistent_count}")
    print(f"Output: {out}")
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", type=int, nargs="?", metavar="N", const=10, default=0, help="Run on first N records only (e.g. --demo 5 or --demo for 10)")
    args = parser.parse_args()

    base = Path(__file__).parent
    run_audits(
        json_path=base / "ehr_messy.json",
        output_csv=base / "audit_report.csv",
        demo_n=args.demo,
    )


if __name__ == "__main__":
    main()
