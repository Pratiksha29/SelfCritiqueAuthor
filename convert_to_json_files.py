#!/usr/bin/env python3
"""
Convert existing audit CSV to individual JSON files to preserve full grievance reports.
This solves the truncation issue by extracting full text from CSV cells.
"""

import csv
import json
import pandas as pd
from pathlib import Path

def convert_audit_csv_to_individual_jsons(csv_path: str, output_dir: str = "grievance_reports"):
    """Convert audit CSV to individual JSON files preserving full grievance reports."""
    
    # Read CSV with proper handling of quoted fields
    df = pd.read_csv(csv_path, quoting=csv.QUOTE_ALL, encoding='utf-8')
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"📁 Converting {len(df)} records to individual JSON files...")
    
    converted_count = 0
    for _, row in df.iterrows():
        patient_id = row['Patient_ID']
        
        # Create comprehensive grievance data
        grievance_data = {
            'patient_info': {
                'Name': row['Name'],
                'Age': row['Age'],
                'Gender': row['Gender'],
                'Blood Type': row['Blood Type'],
                'Medical Condition': row['Medical Condition'],
                'Date of Admission': row['Date of Admission'],
                'Doctor': row['Doctor'],
                'Hospital': row['Hospital'],
                'Insurance Provider': row['Insurance Provider'],
                'Billing Amount': row['Billing Amount'],
                'Room Number': row['Room Number'],
                'Admission Type': row['Admission Type'],
                'Discharge Date': row['Discharge Date'],
                'Medication': row['Medication'],
                'Test Results': row['Test Results'],
                'Patient_ID': row['Patient_ID'],
                'Date_of_Birth': row['Date_of_Birth'],
                'Weight': row['Weight'],
                'Height': row['Height'],
                'cell_number': row['cell_number']
            },
            'audit_status': row['Consistent_or_Not'],
            'grievance_report': row['Grievance_Report'],
            'timestamp': pd.Timestamp.now().isoformat(),
            'full_report_preserved': True
        }
        
        # Save individual JSON file
        file_path = output_path / f"{patient_id}_full_grievance.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(grievance_data, f, indent=2, ensure_ascii=False)
        
        converted_count += 1
        print(f"✅ Saved: {file_path}")
        
        # Show preview of grievance report length
        grievance_length = len(str(row['Grievance_Report']))
        print(f"   📄 Grievance length: {grievance_length} characters")
    
    # Also create a summary file
    summary = {
        'conversion_date': pd.Timestamp.now().isoformat(),
        'total_records': len(df),
        'converted_records': converted_count,
        'output_directory': str(output_path),
        'files_created': [f"{row['Patient_ID']}_full_grievance.json" for _, row in df.iterrows()]
    }
    
    summary_path = output_path / "conversion_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Conversion complete!")
    print(f"📊 Total records: {len(df)}")
    print(f"📁 Output directory: {output_path}")
    print(f"📋 Summary file: {summary_path}")
    
    return output_path

def main():
    """Main function to convert audit CSV to JSON files."""
    csv_path = "audit_report.csv"
    
    if not Path(csv_path).exists():
        print(f"❌ Error: {csv_path} not found!")
        print("Please run the auditor first to generate the audit report.")
        return
    
    output_dir = convert_audit_csv_to_individual_jsons(csv_path)
    
    print(f"\n📖 Usage:")
    print(f"   View individual grievance: grievance_reports/PID-000000_full_grievance.json")
    print(f"   View summary: grievance_reports/conversion_summary.json")

if __name__ == "__main__":
    main()
