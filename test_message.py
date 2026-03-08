#!/usr/bin/env python3
"""Test the actual WhatsApp messages with current parsing"""

import sys
sys.path.append('/Users/pratikshasharma/Documents/Projects/SelfCritiqueAuthor')

from whatsapp_verifier import WhatsAppVerifier
import pandas as pd

# Read audit report
audit_df = pd.read_csv('/Users/pratikshasharma/Documents/Projects/SelfCritiqueAuthor/audit_report.csv')
inconsistent_records = audit_df[audit_df['Consistent_or_Not'] == 'Not Consistent']

verifier = WhatsAppVerifier()

# Test message formatting for first record
first_record = inconsistent_records.iloc[0]
grievance_report = first_record['Grievance_Report']
details = verifier.extract_grievance_details(grievance_report)

print("=== WHATSAPP MESSAGE TEST ===")
print(f"Total inconsistencies: {details['total_inconsistencies']}")
print(f"Number of parsed inconsistencies: {len(details['inconsistencies'])}")

# Generate the actual WhatsApp message
message = verifier._format_user_data_message(details, first_record.to_dict())
print("\n=== GENERATED WHATSAPP MESSAGE ===")
print(message)
