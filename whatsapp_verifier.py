"""
WhatsApp Verification System for EHR grievances.
Sends messages to patients to verify inconsistencies found during audit.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class GrievanceType(Enum):
    USER_DATA = "user_data"  # Issues with patient-provided data (name, DOB, contact)
    CLINICAL_DATA = "clinical_data"  # Issues with diagnosis/treatment (requires doctor verification)


@dataclass
class WhatsAppMessage:
    patient_id: str
    phone_number: str
    message: str
    grievance_type: GrievanceType
    options: List[str]
    grievance_details: Dict[str, Any]


class WhatsAppVerifier:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize WhatsApp verifier.
        For demo purposes, this simulates WhatsApp sending and stores messages/responses to files.
        In production, integrate with WhatsApp Business API.
        """
        self.api_key = api_key
        self.sent_messages = []
        self.responses = {}
        self.message_dir = Path("whatsapp_messages")
        self.message_dir.mkdir(exist_ok=True)
    
    def _send_whatsapp_message(self, phone: str, message: str, patient_id: str = None, grievance_data: Dict = None) -> bool:
        """
        Simulate sending WhatsApp message and save to file with message/response fields.
        In production, use WhatsApp Business API.
        """
        # Create message record
        message_record = {
            'patient_id': patient_id,
            'phone_number': phone,
            'message': message,
            'grievance_type': grievance_data.get('type', 'user_data') if grievance_data else 'user_data',
            'grievance_details': grievance_data,
            'sent_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': time.time(),
            'status': 'sent'
        }
        
        # Save message to file
        if patient_id:
            file_path = self.message_dir / f"{patient_id}_whatsapp.json"
            
            # Check if file exists to append responses
            existing_data = {}
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except:
                    existing_data = {}
            
            # Update or create the record
            if 'messages' not in existing_data:
                existing_data['messages'] = []
            if 'responses' not in existing_data:
                existing_data['responses'] = []
            
            existing_data['messages'].append(message_record)
            existing_data['patient_info'] = grievance_data.get('patient_info', {}) if grievance_data else {}
            
            # Save updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Message saved to: {file_path}")
        
        # Print to console (existing behavior)
        print(f"📱 Sending WhatsApp to {phone}:")
        print(f"Message: {message}")
        
        # Simulate API call delay
        time.sleep(1)
        return True
    
    def _format_user_data_message(self, grievance: Dict, patient_data: Dict) -> str:
        """Format message for user data verification."""
        total_issues = grievance.get('total_inconsistencies', 0)
        inconsistencies = grievance.get('inconsistencies', [])
        
        # Build issue text with specific details
        if total_issues > 1 and inconsistencies:
            issue_lines = ["📋 Issues found:"]
            for i, issue in enumerate(inconsistencies[:3], 1):  # Show first 3 issues
                # Clean up the issue text
                clean_issue = issue.strip()
                if clean_issue and clean_issue[0].isdigit():
                    clean_issue = '.'.join(clean_issue.split('.')[1:]).strip()
                issue_lines.append(f"{i}. {clean_issue}")
            
            if total_issues > 3:
                issue_lines.append(f"... and {total_issues - 3} more issues")
            
            issue_text = '\n'.join(issue_lines)
        elif inconsistencies:
            # Single issue
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
        
        # Build issue text with specific details
        if total_issues > 1 and inconsistencies:
            issue_lines = ["📋 Clinical issues found:"]
            for i, issue in enumerate(inconsistencies[:3], 1):  # Show first 3 issues
                # Clean up the issue text
                clean_issue = issue.strip()
                if clean_issue and clean_issue[0].isdigit():
                    clean_issue = '.'.join(clean_issue.split('.')[1:]).strip()
                issue_lines.append(f"{i}. {clean_issue}")
            
            if total_issues > 3:
                issue_lines.append(f"... and {total_issues - 3} more clinical issues")
            
            issue_text = '\n'.join(issue_lines)
        elif inconsistencies:
            # Single issue
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
        """
        Categorize grievance based on content.
        User data: name, DOB, contact, demographics
        Clinical data: diagnosis, treatment, medications, test results
        """
        grievance_lower = grievance_report.lower()
        
        user_data_keywords = [
            'name', 'date of birth', 'birth', 'age', 'gender', 'blood type',
            'contact', 'phone', 'address', 'insurance', 'billing'
        ]
        
        clinical_data_keywords = [
            'diagnosis', 'treatment', 'medication', 'test result', 'lab',
            'vital', 'blood pressure', 'temperature', 'clinical', 'medical condition'
        ]
        
        # Check for user data issues
        for keyword in user_data_keywords:
            if keyword in grievance_lower:
                return GrievanceType.USER_DATA
        
        # Check for clinical data issues
        for keyword in clinical_data_keywords:
            if keyword in grievance_lower:
                return GrievanceType.CLINICAL_DATA
        
        # Default to clinical data for safety
        return GrievanceType.CLINICAL_DATA
    
    def extract_grievance_details(self, grievance_report: str) -> Dict[str, Any]:
        """Extract structured information from CoVE format grievance report."""
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
                    # Extract just the number at the beginning
                    count_str = count_part.split()[0]
                    details['total_inconsistencies'] = int(count_str)
                except:
                    pass
        
        # Look for numbered items in the text (even if truncated)
        full_text = ' '.join(lines)
        
        # Find all numbered items like "1. Temporal inconsistency"
        import re
        numbered_items = re.findall(r'\d+\.\s+([^0-9]+?)(?=\s+\d+\.|$)', full_text)
        
        if numbered_items:
            for item in numbered_items:
                clean_item = item.strip()
                if clean_item and len(clean_item) > 10:  # Filter out very short fragments
                    details['inconsistencies'].append(clean_item)
        
        # If no numbered items found, try to extract from the main text
        if not details['inconsistencies']:
            # Look for key inconsistency patterns
            patterns = [
                r'Temporal inconsistency[^.]*',
                r'Structural inconsistency[^.]*', 
                r'Clinical contradiction[^.]*',
                r'inconsistency[^.]*',
                r'contradiction[^.]*'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    clean_match = match.strip()
                    if clean_match and len(clean_match) > 15:
                        details['inconsistencies'].append(clean_match)
        
        # If still no inconsistencies, create generic ones based on the count
        if not details['inconsistencies'] and details['total_inconsistencies'] > 0:
            common_issues = [
                "Temporal inconsistency between dates",
                "Name formatting issue", 
                "Clinical data contradiction",
                "Missing required information",
                "Data entry error detected"
            ]
            
            for i in range(min(details['total_inconsistencies'], len(common_issues))):
                details['inconsistencies'].append(common_issues[i])
        
        # Create a summary issue from first inconsistency
        if details['inconsistencies']:
            first_issue = details['inconsistencies'][0]
            # Clean up any remaining numbering
            if first_issue and first_issue[0].isdigit():
                parts = first_issue.split('.', 1)
                if len(parts) > 1:
                    first_issue = parts[1].strip()
            details['issue'] = first_issue
        
        # Generate question based on issue
        if details['issue']:
            details['question'] = f"Is this correct: {details['issue']}?"
        elif details['total_inconsistencies'] > 0:
            details['issue'] = f"{details['total_inconsistencies']} data inconsistencies found in your medical records"
            details['question'] = "We found several inconsistencies in your records. Can you help us verify them?"
        
        return details
    
    def send_verification_messages(self, audit_csv_path: Union[str, Path]) -> List[WhatsAppMessage]:
        """
        Send WhatsApp messages for all inconsistent records.
        """
        audit_df = pd.read_csv(audit_csv_path)
        inconsistent_records = audit_df[audit_df['Consistent_or_Not'] == 'Not Consistent']
        
        messages = []
        
        for _, record in inconsistent_records.iterrows():
            patient_id = record.get('Patient_ID', '')
            phone = record.get('cell_number', '')
            
            if not phone:
                print(f"⚠️ No phone number for Patient {patient_id}, skipping WhatsApp verification")
                continue
            
            grievance_report = record.get('Grievance_Report', '')
            grievance_type = self.categorize_grievance(grievance_report)
            grievance_details = self.extract_grievance_details(grievance_report)
            
            # Format message based on type
            if grievance_type == GrievanceType.USER_DATA:
                message_text = self._format_user_data_message(grievance_details, record.to_dict())
                options = ['YES', 'NO', 'DETAILS']
            else:
                message_text = self._format_clinical_data_message(grievance_details, record.to_dict())
                options = ['CONFIRM', 'DECLINE', 'DETAILS']
            
            # Create message object
            message = WhatsAppMessage(
                patient_id=patient_id,
                phone_number=phone,
                message=message_text,
                grievance_type=grievance_type,
                options=options,
                grievance_details=grievance_details
            )
            
            # Send message
            grievance_data = {
                'type': grievance_type.value,
                'patient_info': record.to_dict(),
                'grievance_details': grievance_details
            }
            
            if self._send_whatsapp_message(phone, message_text, patient_id, grievance_data):
                messages.append(message)
                self.sent_messages.append(message)
                print(f"✅ Message sent to Patient {patient_id}")
            else:
                print(f"❌ Failed to send message to Patient {patient_id}")
        
        return messages
    
    def record_response(self, patient_id: str, response: str) -> bool:
        """
        Record patient response to WhatsApp message and save to file.
        """
        # Add to memory
        if patient_id not in self.responses:
            self.responses[patient_id] = []
        
        response_record = {
            'response': response,
            'timestamp': time.time(),
            'received_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self.responses[patient_id].append(response_record)
        
        # Save to file alongside messages
        file_path = self.message_dir / f"{patient_id}_whatsapp.json"
        
        # Read existing data
        existing_data = {}
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                existing_data = {}
        
        # Ensure responses array exists
        if 'responses' not in existing_data:
            existing_data['responses'] = []
        
        # Add response
        existing_data['responses'].append(response_record)
        
        # Save updated data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Response saved to: {file_path}")
        print(f"📝 Recorded response from Patient {patient_id}: {response}")
        return True
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """
        Get summary of verification process.
        """
        total_sent = len(self.sent_messages)
        total_responded = len(self.responses)
        
        summary = {
            'total_messages_sent': total_sent,
            'total_responses_received': total_responded,
            'response_rate': (total_responded / total_sent * 100) if total_sent > 0 else 0,
            'responses_by_patient': self.responses,
            'sent_messages': [
                {
                    'patient_id': msg.patient_id,
                    'phone': msg.phone_number,
                    'type': msg.grievance_type.value,
                    'options': msg.options
                }
                for msg in self.sent_messages
            ]
        }
        
        return summary


def main():
    """Demo function to test WhatsApp verification."""
    verifier = WhatsAppVerifier()
    
    # Test with audit report
    audit_path = Path(__file__).parent / "audit_report.csv"
    if audit_path.exists():
        print("🚀 Starting WhatsApp verification process...")
        messages = verifier.send_verification_messages(audit_path)
        print(f"✅ Sent {len(messages)} WhatsApp messages")
        
        # Demo responses
        for msg in messages[:2]:  # Simulate responses for first 2 patients
            verifier.record_response(msg.patient_id, "YES")
        
        summary = verifier.get_verification_summary()
        print("\n📊 Verification Summary:")
        print(json.dumps(summary, indent=2))
    else:
        print(f"❌ Audit report not found at {audit_path}")


if __name__ == "__main__":
    main()
