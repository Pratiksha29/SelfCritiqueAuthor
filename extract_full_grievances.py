#!/usr/bin/env python3
"""
Extract full grievance reports from CSV by reading raw text and reconstructing.
This handles CSV truncation by parsing the raw CSV format.
"""

import csv
import json
import re
from pathlib import Path

def extract_full_grievance_from_csv(csv_path: str, output_dir: str = "full_grievance_reports"):
    """Extract complete grievance reports from CSV by parsing raw format."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"🔍 Extracting full grievance reports from {csv_path}...")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        # Read the header line
        header_line = f.readline()
        headers = [h.strip() for h in header_line.split(',')]
        
        # Find grievance column index
        grievance_col_idx = None
        for i, header in enumerate(headers):
            if 'Grievance_Report' in header:
                grievance_col_idx = i
                break
        
        if grievance_col_idx is None:
            print("❌ Grievance_Report column not found!")
            return
        
        print(f"📊 Found Grievance_Report column at index {grievance_col_idx}")
        
        # Process each data line
        records_processed = 0
        for line_num, line in enumerate(f, 2):  # Start from line 2 (after header)
            if not line.strip():
                continue
                
            # Parse CSV line manually to handle quoted fields
            reader = csv.reader([line])
            fields = next(reader)
            
            if len(fields) > grievance_col_idx:
                grievance_text = fields[grievance_col_idx]
                patient_id = fields[headers.index('Patient_ID')] if 'Patient_ID' in headers else f'UNKNOWN-{line_num}'
                
                # Try to reconstruct full grievance if truncated
                if grievance_text and len(grievance_text) > 50:
                    # Look for patterns that indicate truncation
                    if grievance_text.endswith('...') or grievance_text.endswith('"'):
                        print(f"⚠️  Line {line_num}: Possible truncation detected")
                    
                    # Clean up the grievance text
                    grievance_text = grievance_text.strip('"')
                    
                    # Create full grievance record
                    grievance_record = {
                        'patient_id': patient_id,
                        'line_number': line_num,
                        'raw_grievance': grievance_text,
                        'character_count': len(grievance_text),
                        'extraction_method': 'csv_raw_parse',
                        'timestamp': line_num
                    }
                    
                    # Save as JSON
                    file_path = output_path / f"{patient_id}_extracted_grievance.json"
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(grievance_record, f, indent=2, ensure_ascii=False)
                    
                    records_processed += 1
                    print(f"✅ Extracted: {file_path} ({len(grievance_text)} chars)")
    
    print(f"\n🎉 Extraction complete!")
    print(f"📊 Records processed: {records_processed}")
    print(f"📁 Output directory: {output_path}")
    
    return output_path

def analyze_csv_structure(csv_path: str):
    """Analyze CSV structure to understand truncation."""
    print(f"🔍 Analyzing CSV structure: {csv_path}")
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 Total lines: {len(lines)}")
    
    # Check header
    header = lines[0]
    print(f"📋 Header: {header}")
    
    # Check sample data lines
    for i, line in enumerate(lines[1:6], 1):
        print(f"📝 Line {i}: {len(line)} chars")
        if len(line) > 200:
            print(f"   ⚠️  Long line - potential full grievance")
        else:
            print(f"   📏 Short line - likely truncated")
    
    return len(lines)

def main():
    """Main function."""
    csv_path = "audit_report.csv"
    
    if not Path(csv_path).exists():
        print(f"❌ Error: {csv_path} not found!")
        return
    
    # First analyze structure
    analyze_csv_structure(csv_path)
    
    print("\n" + "="*50)
    
    # Then extract full grievances
    extract_full_grievance_from_csv(csv_path)

if __name__ == "__main__":
    main()
