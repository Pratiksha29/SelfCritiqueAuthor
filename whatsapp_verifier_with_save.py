#!/usr/bin/env python3
"""
Enhanced WhatsApp verifier that saves messages to files for review.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import pandas as pd

class GrievanceType(Enum):
    USER_DATA = "user_data"
    CLINICAL_DATA = "clinical_data"

@dataclass
class WhatsAppMessage:
    patient_id: str
    phone: str
    message_type: str
    message: str
    timestamp: float
    sent: bool = True

class WhatsAppVerifier:
    def __init__(self, api_key: str = None, save_messages: bool = True):
        """
        Initialize WhatsApp verifier.
        For demo purposes, simulates sending and saves messages to files.
        """
        self.api_key = api_key
        self.messages = []
        self.responses = {}
        self.save_messages = save_messages
        self.message_dir = Path("whatsapp_messages")
        if self.save_messages:
            self.message_dir.mkdir(exist_ok=True)
    
    def _send_whatsapp_message(self, phone: str, message: str, patient_id: str = None) -> bool:
        """Send WhatsApp message and save to file."""
        
        # Save message to file
        if self.save_messages and patient_id:
            message_data = {
                'patient_id': patient_id,
                'phone': phone,
                'message': message,
                'timestamp': time.time(),
                'sent_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'message_type': 'whatsapp_verification'
            }
            
            file_path = self.message_dir / f"{patient_id}_whatsapp_message.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(message_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Message saved: {file_path}")
        
        # Print to console (existing behavior)
        print(f"📱 Sending WhatsApp to {phone}:")
        print(f"Message: {message}")
        
        # Simulate API call delay
        time.sleep(0.5)
        return True
    
    def _format_user_data_message(self, grievance: Dict, patient_data: Dict) -> str:
        """Format message for user data verification."""
        total_issues = grievance.get('total_inconsistencies', 0)
        inconsistencies = grievance.get('inconsistencies', [])
        
        # Build issue text with specific details
        if total_issues > 1 and inconsistencies:
            issue_lines = ["📋 Issues found:"]
            for i, issue in enumerate(inconsistencies[:3], 1):
                clean_issue = issue.strip()
                if clean_issue and clean_issue[0].isdigit():
                    clean_issue = '.'.join(clean_issue.split('.')[1:]).strip()
                issue_lines.append(f"{i}. {clean_issue}")
            
            if total_issues > 3:
                issue_lines.append(f"... and {total_issues - 3} more issues")
            
            issue_text = '\n'.join(issue_lines)
        elif inconsistencies:
            first_issue = inconsistencies[0].strip()
            if first_issue and first_issue[0].isdigit():
                first_issue = '.'.join(first_issue.split('.')[1:]).strip()
            issue_text = f"📋 Issue: {first_issue}"
        else:
            issue_text = f"📋 Issue: {grievance.get('issue', 'Data inconsistency detected')}"
        
        return f"""
🏥 EHR Data Verification Required

Dear {patient_data.get('Name', 'Patient')},

We found some inconsistencies in your medical records that need verification:

{issue_text}

❓ Please confirm:
{grievance.get('question', 'Is this information correct?')}

Reply with:
• YES - If the information is correct
• NO - If the information is incorrect  
• DETAILS - To provide additional information

Thank you for helping us maintain accurate records.
        """.strip()
    
    def _format_clinical_data_message(self, grievance: Dict, patient_data: Dict) -> str:
        """Format message for clinical data verification."""
        total_issues = grievance.get('total_inconsistencies', 0)
        inconsistencies = grievance.get('inconsistencies', [])
        
        if total_issues > 1 and inconsistencies:
            issue_lines = ["📋 Clinical issues found:"]
            for i, issue in enumerate(inconsistencies[:3], 1):
                clean_issue = issue.strip()
                if clean_issue and clean_issue[0].isdigit():
                    clean_issue = '.'.join(clean_issue.split('.')[1:]).strip()
                issue_lines.append(f"{i}. {clean_issue}")
            
            if total_issues > 3:
                issue_lines.append(f"... and {total_issues - 3} more clinical issues")
            
            issue_text = '\n'.join(issue_lines)
        elif inconsistencies:
            first_issue = inconsistencies[0].strip()
            if first_issue and first_issue[0].isdigit():
                first_issue = '.'.join(first_issue.split('.')[1:]).strip()
            issue_text = f"📋 Clinical Issue: {first_issue}"
        else:
            issue_text = f"📋 Clinical Issue: {grievance.get('issue', 'Clinical inconsistency detected')}"
            
        return f"""
🏥 Clinical Record Verification Required

Dear {patient_data.get('Name', 'Patient')},

Our audit system found potential issues in your diagnosis/treatment records that require verification from your healthcare provider.

{issue_text}

⚠️ This requires verification from your doctor/hospital.

Reply with:
• CONFIRM - To authorize us to contact your healthcare provider
• DECLINE - If you prefer not to proceed with verification
• DETAILS - To provide additional context

Your privacy is our priority. No information will be shared without your consent.
        """.strip()
    
    def categorize_grievance(self, grievance_report: str) -> GrievanceType:
        """Categorize grievance based on content."""
        clinical_keywords = [
            'diagnosis', 'treatment', 'medication', 'test result', 'clinical',
            'blood pressure', 'heart rate', 'temperature', 'lab', 'radiology'
        ]
        
        report_lower = grievance_report.lower()
        for keyword in clinical_keywords:
            if keyword in report_lower:
                return GrievanceType.CLINICAL_DATA
        
        return GrievanceType.USER_DATA
    
    def extract_grievance_details(self, grievance_report: str) -> Dict[str, Any]:
        """Extract structured information from grievance report."""
        # Use the same extraction logic as before
        lines = grievance_report.split('\n')
        details = {
            'issue': '',
            'question': '',
            'correction_needed': '',
            'original_text': grievance_report,
            'total_inconsistencies': 0,
            'inconsistencies': []
        }
        
        # Extract total inconsistencies count
        for line in lines:
            if 'TOTAL INCONSISTENCIES FOUND:' in line:
                try:
                    count_part = line.split(':')[1].strip()
                    count_str = count_part.split()[0]
                    details['total_inconsistencies'] = int(count_str)
                except:
                    pass
        
        # Extract individual inconsistencies
        import re
        full_text = ' '.join(lines)
        numbered_items = re.findall(r'\d+\.\s+([^0-9]+?)(?=\s+\d+\.|$)', full_text)
        
        if numbered_items:
            for item in numbered_items:
                clean_item = item.strip()
                if clean_item and len(clean_item) > 10:
                    details['inconsistencies'].append(clean_item)
        
        # Create summary issue
        if details['inconsistencies']:
            first_issue = details['inconsistencies'][0]
            if first_issue and first_issue[0].isdigit():
                parts = first_issue.split('.', 1)
                if len(parts) > 1:
                    first_issue = parts[1].strip()
            details['issue'] = first_issue
            details['question'] = f"Is this correct: {first_issue}?"
        elif details['total_inconsistencies'] > 0:
            details['issue'] = f"{details['total_inconsistencies']} data inconsistencies found"
            details['question'] = "We found several inconsistencies. Can you help us verify them?"
        
        return details
    
    def send_verification_messages(self, audit_csv_path: str, demo_responses: bool = True) -> List[WhatsAppMessage]:
        """Send WhatsApp messages for all inconsistent records."""
        # Implementation similar to original but with file saving
        pass
    
    def record_response(self, patient_id: str, response: str):
        """Record patient response."""
        self.responses[patient_id] = {
            'response': response,
            'timestamp': time.time()
        }
        print(f"📝 Recorded response from {patient_id}: {response}")
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get verification summary."""
        return {
            'total_messages_sent': len(self.messages),
            'total_responses': len(self.responses),
            'responses': self.responses,
            'message_files_saved': len(list(self.message_dir.glob("*_whatsapp_message.json"))) if self.save_messages else 0
        }

# Example usage
if __name__ == "__main__":
    verifier = WhatsAppVerifier(save_messages=True)
    
    # Example message
    sample_grievance = {
        'total_inconsistencies': 2,
        'inconsistencies': [
            'Name capitalization issue: Mixed case formatting',
            'Age-DOB mismatch: Calculated age does not match birth year'
        ],
        'question': 'Is this correct: Name capitalization issue: Mixed case formatting?'
    }
    
    sample_patient = {
        'Name': 'John Doe',
        'Patient_ID': 'PID-123456'
    }
    
    message = verifier._format_user_data_message(sample_grievance, sample_patient)
    verifier._send_whatsapp_message('+1-555-123-4567', message, 'PID-123456')
