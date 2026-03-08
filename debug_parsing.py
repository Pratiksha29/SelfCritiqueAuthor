#!/usr/bin/env python3
"""Debug script to test grievance parsing"""

import sys
sys.path.append('/Users/pratikshasharma/Documents/Projects/SelfCritiqueAuthor')

from whatsapp_verifier import WhatsAppVerifier
import pandas as pd

# Read audit report
audit_df = pd.read_csv('/Users/pratikshasharma/Documents/Projects/SelfCritiqueAuthor/audit_report.csv')
inconsistent_records = audit_df[audit_df['Consistent_or_Not'] == 'Not Consistent']

verifier = WhatsAppVerifier()

# Test parsing for first record
first_record = inconsistent_records.iloc[0]
grievance_report = first_record['Grievance_Report']

print("=== ORIGINAL GRIEVANCE REPORT ===")
print(grievance_report)
print("\n" + "="*50 + "\n")

# Parse the grievance
details = verifier.extract_grievance_details(grievance_report)

print("=== PARSED DETAILS ===")
print(f"Total inconsistencies: {details['total_inconsistencies']}")
print(f"Issue: {details['issue']}")
print(f"Question: {details['question']}")
print(f"Inconsistencies found: {len(details['inconsistencies'])}")

print("\n=== INCONSISTENCY LIST ===")
for i, inconsistency in enumerate(details['inconsistencies']):
    print(f"{i+1}. {inconsistency}")
