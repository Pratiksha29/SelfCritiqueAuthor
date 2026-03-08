#!/usr/bin/env python3
"""
Store each grievance report in separate JSON files to avoid truncation.
"""

import json
import pandas as pd
from pathlib import Path

def save_individual_grievances(csv_path: str, output_dir: str = "grievance_reports"):
    """Save each grievance report as individual JSON file."""
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save each grievance report
    for _, row in df.iterrows():
        if row['Consistent_or_Not'] == 'Not Consistent':
            patient_id = row['Patient_ID']
            grievance_data = {
                'patient_info': row.to_dict(),
                'grievance_report': row['Grievance_Report'],
                'full_report_stored': True
            }
            
            # Save individual file
            file_path = output_path / f"{patient_id}_grievance.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(grievance_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Saved grievance for {patient_id}: {file_path}")
    
    print(f"\n📁 All grievance reports saved to: {output_path}/")

if __name__ == "__main__":
    save_individual_grievances("audit_report.csv")
