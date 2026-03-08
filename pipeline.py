"""
EHR pipeline: one file with four functions that run the full flow.

1. load_csv_to_json() — Read CSV and write JSON (same as main.py).
2. run_audits()       — Run auditor on each record; produce audit_report.csv (same as run_auditor.py).
3. run_verification()  — Send WhatsApp messages and doctor verification requests for inconsistencies.
4. run_resolver()     — Correct inconsistent data from grievance reports (resolver.py); produce ehr_corrected.csv/json.
"""

from pathlib import Path
from typing import Union

# Base directory for default paths
BASE = Path(__file__).parent


def load_csv_to_json(
    csv_path: Union[str, Path] = None,
    json_path: Union[str, Path] = None,
) -> Path:
    """
    Read EHR data from CSV and save as JSON for the auditor.
    """
    import json
    import pandas as pd
    
    csv_path = csv_path or BASE / "ehr_messy.csv"
    json_path = json_path or BASE / "ehr_messy.json"
    
    # Read CSV and convert to JSON
    df = pd.read_csv(csv_path)
    data = df.to_dict(orient='records')
    
    # Save as JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {csv_path} to {json_path} ({len(data)} records)")
    return Path(json_path)


def run_audits(
    json_path: Union[str, Path] = None,
    output_csv: Union[str, Path] = None,
    demo_n: int = 0,
) -> Path:
    """
    Run the auditor on each record in the JSON file; write audit_report.csv
    with columns Consistent_or_Not and Grievance_Report.
    """
    import json
    import pandas as pd
    import time
    import os
    from pathlib import Path
    
    json_path = json_path or BASE / "ehr_messy.json"
    output_csv = output_csv or BASE / "audit_report.csv"
    
    # Load data
    with open(json_path, 'r') as f:
        records = json.load(f)
    
    if demo_n > 0:
        records = records[:demo_n]
        print(f"Demo mode: auditing first {len(records)} records only")
    
    # Use the JSON auditor instead
    print("🔍 Running JSON auditor for complete grievance reports...")
    from run_auditor_json_complete import run_auditor_json_only
    
    # Run the JSON auditor which creates individual JSON files
    grievance_dir = run_auditor_json_only(json_path=json_path, demo_n=demo_n)
    
    # Create a summary CSV for compatibility
    print("📋 Creating summary CSV for compatibility...")
    summary_data = []
    
    for record in records:
        patient_id = record.get('Patient_ID', '')
        
        # Try to load the grievance report
        grievance_file = grievance_dir / f"{patient_id}_complete_grievance.json"
        if grievance_file.exists():
            try:
                with open(grievance_file, 'r') as f:
                    grievance_data = json.load(f)
                
                audit_results = grievance_data.get('audit_results', {})
                status = audit_results.get('status', 'Consistent')
                grievance_report = audit_results.get('grievance_report', 'No issues found')
                
                summary_data.append({
                    'Patient_ID': patient_id,
                    'Consistent_or_Not': status,
                    'Grievance_Report': grievance_report
                })
            except Exception as e:
                print(f"⚠️ Could not load grievance for {patient_id}: {e}")
                summary_data.append({
                    'Patient_ID': patient_id,
                    'Consistent_or_Not': 'Consistent',
                    'Grievance_Report': 'No grievance available'
                })
        else:
            summary_data.append({
                'Patient_ID': patient_id,
                'Consistent_or_Not': 'Consistent',
                'Grievance_Report': 'No grievance file found'
            })
    
    # Save summary CSV
    df = pd.DataFrame(summary_data)
    df.to_csv(output_csv, index=False)
    
    inconsistent_count = len([r for r in summary_data if r['Consistent_or_Not'] == 'Not Consistent'])
    print(f"✅ Audit complete: {len(summary_data)} records processed, {inconsistent_count} inconsistent")
    print(f"📁 Summary CSV: {output_csv}")
    print(f"📁 Detailed grievances: {grievance_dir}")
    
    return Path(output_csv)


def run_resolver(
    audit_csv: Union[str, Path] = None,
    output_csv: Union[str, Path] = None,
    output_json: Union[str, Path] = None,
):
    """
    Correct inconsistent data based on grievance reports in audit_report.csv.
    Writes ehr_corrected.csv and ehr_corrected.json (no audit columns).
    Same behavior as resolver.py.
    """
    from resolver import resolve
    audit_csv = audit_csv or BASE / "audit_report.csv"
    output_csv = output_csv or BASE / "ehr_corrected.csv"
    output_json = output_json or BASE / "ehr_corrected.json"
    return resolve(
        audit_csv_path=audit_csv,
        output_csv_path=output_csv,
        output_json_path=output_json,
    )


def run_verification(
    grievance_dir: Union[str, Path] = None,
    demo_responses: bool = False,
) -> dict:
    """
    Run verification process for inconsistent records.
    Sends WhatsApp messages to patients and verification requests to doctors.
    Returns verification summary.
    """
    from whatsapp_verifier import WhatsAppVerifier
    from doctor_verifier import DoctorVerifier
    import json
    import glob
    
    grievance_dir = grievance_dir or BASE / "grievance_reports"
    
    # Initialize verifiers
    whatsapp_verifier = WhatsAppVerifier()
    doctor_verifier = DoctorVerifier()
    
    print("🚀 Starting verification process...")
    
    # Load grievance reports from JSON files
    print("\n📋 Loading grievance reports...")
    grievance_files = glob.glob(str(grievance_dir / "*_complete_grievance.json"))
    
    if not grievance_files:
        print("❌ No grievance reports found! Run the auditor first.")
        return {"error": "No grievance reports found"}
    
    grievances = []
    for file_path in grievance_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                grievances.append(data)
        except Exception as e:
            print(f"⚠️ Could not load {file_path}: {e}")
    
    print(f"✅ Loaded {len(grievances)} grievance reports")
    
    # Filter for inconsistent records
    inconsistent_grievances = [g for g in grievances if g.get('audit_results', {}).get('status') == 'Not Consistent']
    print(f"📊 Found {len(inconsistent_grievances)} inconsistent records")
    
    # Send WhatsApp messages to patients
    if inconsistent_grievances:
        print("\n📱 Sending WhatsApp messages to patients...")
        whatsapp_messages = whatsapp_verifier.send_verification_messages_json(inconsistent_grievances)
    else:
        whatsapp_messages = []
        print("\n✅ No inconsistent records - no WhatsApp messages needed")
    
    # Send doctor verification requests for clinical issues
    doctor_requests = []
    if inconsistent_grievances:
        print("\n📧 Sending verification requests to doctors...")
        for grievance in inconsistent_grievances:
            # Check if there are clinical issues
            if 'clinical' in grievance.get('audit_results', {}).get('grievance_report', '').lower():
                request = doctor_verifier.send_verification_request(grievance)
                if request:
                    doctor_requests.append(request)
    
    # Simulate demo responses
    if demo_responses and inconsistent_grievances:
        print("\n🎭 Simulating demo responses...")
        import random
        import time
        
        responses = ['YES', 'NO', 'DETAILS', 'CONFIRM', 'DECLINE']
        for i, grievance in enumerate(inconsistent_grievances[:3]):  # Simulate first 3
            patient_id = grievance['patient_info']['Patient_ID']
            response = random.choice(responses)
            whatsapp_verifier.record_response(patient_id, response)
            print(f"💾 Response saved: {patient_id} -> {response}")
            time.sleep(0.1)
    
    # Return verification summary
    summary = {
        "total_grievances": len(grievances),
        "inconsistent_records": len(inconsistent_grievances),
        "whatsapp_messages_sent": len(whatsapp_messages),
        "doctor_requests_sent": len(doctor_requests),
        "demo_responses": demo_responses
    }
    
    print(f"\n✅ Verification complete!")
    print(f"   📊 Total grievances: {summary['total_grievances']}")
    print(f"   ❌ Inconsistent records: {summary['inconsistent_records']}")
    print(f"   📱 WhatsApp messages: {summary['whatsapp_messages_sent']}")
    print(f"   📧 Doctor requests: {summary['doctor_requests_sent']}")
    
    return summary


def run_full_pipeline(
    csv_path: Union[str, Path] = None,
    demo_n: int = 0,
    include_verification: bool = True,
) -> tuple:
    """
    Run the complete pipeline: load data, audit, verify, and resolve.
    Returns tuple of (json_path, audit_csv, corrected_csv, verification_summary).
    """
    # Step 1: Load CSV to JSON
    json_path = load_csv_to_json(csv_path=csv_path)
    
    # Step 2: Run audits
    audit_csv = run_audits(json_path=json_path, demo_n=demo_n)
    
    # Step 3: Run verification (if enabled)
    verification_summary = {}
    if include_verification:
        verification_summary = run_verification(demo_responses=True)
    
    # Step 4: Run resolver
    corrected_csv = run_resolver(audit_csv=audit_csv)
    
    return json_path, audit_csv, corrected_csv, verification_summary


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EHR Audit Pipeline")
    parser.add_argument("--demo", type=int, nargs="?", const=10, default=0,
                       help="Run on first N records only")
    parser.add_argument("--step", choices=["audit", "verify", "resolve"],
                       help="Run specific step only")
    parser.add_argument("--no-verification", action="store_true",
                       help="Skip verification step")
    
    args = parser.parse_args()
    
    if args.step == "audit":
        # Run audit step only
        json_path = load_csv_to_json()
        run_audits(json_path=json_path, demo_n=args.demo)
        
    elif args.step == "verify":
        # Run verification step only
        run_verification(demo_responses=True)
        
    elif args.step == "resolve":
        # Run resolver step only
        run_resolver(demo_n=args.demo)
        
    else:
        # Run full pipeline
        json_path, audit_csv, corrected_csv, verification_summary = run_full_pipeline(
            csv_path=BASE / "ehr_messy.csv",
            demo_n=args.demo,
            include_verification=not args.no_verification
        )
        
        print(f"\n🎉 Pipeline completed!")
        print(f"📁 JSON data: {json_path}")
        print(f"📋 Audit report: {audit_csv}")
        print(f"✅ Corrected data: {corrected_csv}")
        if verification_summary:
            print(f"📱 Verification: {verification_summary.get('whatsapp_messages_sent', 0)} messages sent")
        print(f"📊 Total grievances: {verification_summary.get('total_grievances', 0)}")
        print(f"❌ Inconsistent records: {verification_summary.get('inconsistent_records', 0)}")


def run_full_pipeline_legacy(
    csv_path: Union[str, Path] = None,
    demo_n: int = 0,
    include_verification: bool = True,
):
    """
    Run all four steps: load CSV → JSON, run audits, run verification, run resolver.
    Returns (json_path, audit_csv_path, corrected_csv_path, verification_summary).
    """
    csv_path = csv_path or BASE / "ehr_messy.csv"
    json_path = BASE / "ehr_messy.json"
    audit_csv = BASE / "audit_report.csv"
    corrected_csv = BASE / "ehr_corrected.csv"

    load_csv_to_json(csv_path=csv_path, json_path=json_path)
    run_audits(json_path=json_path, output_csv=audit_csv, demo_n=demo_n)
    
    verification_summary = None
    if include_verification:
        verification_summary = run_verification(demo_responses=True)
    
    run_resolver(audit_csv=audit_csv, output_csv=corrected_csv, output_json=BASE / "ehr_corrected.json")

    return json_path, audit_csv, corrected_csv, verification_summary


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EHR pipeline: load CSV→JSON, run audits, verification, resolver.")
    parser.add_argument("--step", choices=["load", "audit", "verify", "resolve", "all"], default="all", help="Which step(s) to run")
    parser.add_argument("--demo", type=int, default=0, help="For audit step: only process first N records (0 = all)")
    parser.add_argument("--csv", default=None, help="Input CSV for load step (default: ehr_messy.csv)")
    parser.add_argument("--no-verification", action="store_true", help="Skip verification step in full pipeline")
    args = parser.parse_args()

    csv_path = Path(args.csv) if args.csv else BASE / "ehr_messy.csv"

    if args.step == "load":
        load_csv_to_json(csv_path=csv_path, json_path=BASE / "ehr_messy.json")
        print("Done: ehr_messy.json")
    elif args.step == "audit":
        run_audits(json_path=BASE / "ehr_messy.json", output_csv=BASE / "audit_report.csv", demo_n=args.demo)
        print("Done: audit_report.csv")
    elif args.step == "verify":
        run_verification(audit_csv=BASE / "audit_report.csv", demo_responses=True)
        print("Done: verification process")
    elif args.step == "resolve":
        run_resolver(audit_csv=BASE / "audit_report.csv", output_csv=BASE / "ehr_corrected.csv", output_json=BASE / "ehr_corrected.json")
        print("Done: ehr_corrected.csv, ehr_corrected.json")
    else:
        include_verification = not args.no_verification
        json_path, audit_csv, corrected_csv, verification_summary = run_full_pipeline(
            csv_path=csv_path, 
            demo_n=args.demo, 
            include_verification=include_verification
        )
        print("Done: full pipeline.")
