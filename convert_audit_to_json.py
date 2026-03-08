#!/usr/bin/env python3
"""
Convert audit report CSV to JSON format to handle long grievance reports properly.
"""

import pandas as pd
import json
from pathlib import Path

def convert_audit_csv_to_json(csv_path: str, json_path: str = None):
    """Convert audit report from CSV to JSON format."""
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Convert to records
    audit_records = df.to_dict('records')
    
    # Determine output path
    if not json_path:
        csv_path_obj = Path(csv_path)
        json_path = csv_path_obj.parent / f"{csv_path_obj.stem}.json"
    
    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(audit_records, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted {len(audit_records)} records to JSON: {json_path}")
    return json_path

if __name__ == "__main__":
    convert_audit_csv_to_json("audit_report.csv")
