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
    Same behavior as main.py.
    """
    from main import load_csv_to_json as _load
    csv_path = csv_path or BASE / "ehr_messy.csv"
    json_path = json_path or BASE / "ehr_messy.json"
    return _load(csv_path, json_path)


def run_audits(
    json_path: Union[str, Path] = None,
    output_csv: Union[str, Path] = None,
    demo_n: int = 0,
) -> Path:
    """
    Run the auditor on each record in the JSON file; write audit_report.csv
    with columns Consistent_or_Not and Grievance_Report.
    Same behavior as run_auditor.py.
    """
    from run_auditor import run_audits as _audit
    json_path = json_path or BASE / "ehr_messy.json"
    output_csv = output_csv or BASE / "audit_report.csv"
    return _audit(json_path=json_path, output_csv=output_csv, demo_n=demo_n)


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
    audit_csv: Union[str, Path] = None,
    demo_responses: bool = False,
) -> dict:
    """
    Run verification process for inconsistent records.
    Sends WhatsApp messages to patients and verification requests to doctors.
    Returns verification summary.
    """
    from whatsapp_verifier import WhatsAppVerifier
    from doctor_verifier import DoctorVerifier
    
    audit_csv = audit_csv or BASE / "audit_report.csv"
    
    # Initialize verifiers
    whatsapp_verifier = WhatsAppVerifier()
    doctor_verifier = DoctorVerifier()
    
    print("🚀 Starting verification process...")
    
    # Send WhatsApp messages to patients
    print("\n📱 Sending WhatsApp messages to patients...")
    whatsapp_messages = whatsapp_verifier.send_verification_messages(audit_csv)
    
    # Send doctor verification requests for clinical issues
    print("\n📧 Sending verification requests to doctors...")
    import pandas as pd
    audit_df = pd.read_csv(audit_csv)
    inconsistent_records = audit_df[audit_df['Consistent_or_Not'] == 'Not Consistent']
    
    doctor_requests = []
    for _, record in inconsistent_records.iterrows():
        grievance_report = record.get('Grievance_Report', '')
        grievance_type = whatsapp_verifier.categorize_grievance(grievance_report)
        
        if grievance_type.value == 'clinical_data':
            grievance_details = whatsapp_verifier.extract_grievance_details(grievance_report)
            request = doctor_verifier.create_verification_request(
                record.to_dict(), 
                grievance_details, 
                patient_consent=True  # In production, this would come from WhatsApp response
            )
            if doctor_verifier.send_verification_request(request):
                doctor_requests.append(request)
    
    # Demo responses if requested
    if demo_responses:
        print("\n🎭 Simulating demo responses...")
        # Simulate some WhatsApp responses
        for i, msg in enumerate(whatsapp_messages[:2]):
            whatsapp_verifier.record_response(msg.patient_id, 'YES' if i % 2 == 0 else 'DETAILS')
        
        # Simulate some doctor responses
        for i, req in enumerate(doctor_requests[:1]):
            from doctor_verifier import VerificationStatus
            doctor_verifier.record_doctor_response(
                req.patient_id, 
                'CONFIRMED - Clinical information verified', 
                VerificationStatus.CONFIRMED
            )
    
    # Get summaries
    whatsapp_summary = whatsapp_verifier.get_verification_summary()
    doctor_summary = doctor_verifier.get_verification_summary()
    
    combined_summary = {
        'whatsapp_verification': whatsapp_summary,
        'doctor_verification': doctor_summary,
        'total_patients_contacted': len(whatsapp_messages),
        'total_doctors_contacted': len(doctor_requests)
    }
    
    print(f"\n✅ Verification complete!")
    print(f"   📱 WhatsApp messages sent: {len(whatsapp_messages)}")
    print(f"   📧 Doctor requests sent: {len(doctor_requests)}")
    
    return combined_summary


def run_full_pipeline(
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
        verification_summary = run_verification(audit_csv=audit_csv, demo_responses=True)
    
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
        if verification_summary:
            print(f"Verification summary: {verification_summary['total_patients_contacted']} patients contacted, {verification_summary['total_doctors_contacted']} doctors contacted")
