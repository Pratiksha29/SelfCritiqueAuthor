"""
Doctor/Hospital Verification System for clinical grievances.
Handles verification of diagnosis and treatment issues with healthcare providers.
"""

import json
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class VerificationStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    CLARIFICATION_NEEDED = "clarification_needed"


@dataclass
class VerificationRequest:
    patient_id: str
    doctor_name: str
    hospital_name: str
    email: str
    clinical_issue: str
    patient_consent: bool
    grievance_details: Dict[str, Any]
    status: VerificationStatus = VerificationStatus.PENDING
    created_at: float = None
    response: Optional[str] = None


class DoctorVerifier:
    def __init__(self, smtp_config: Optional[Dict] = None):
        """
        Initialize doctor verification system.
        For demo purposes, simulates email sending.
        In production, configure with real SMTP settings.
        """
        self.smtp_config = smtp_config or {
            'server': 'smtp.gmail.com',
            'port': 587,
            'username': 'ehr_system@hospital.com',
            'password': 'your_app_password'
        }
        self.verification_requests = []
        self.responses = {}
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send email to healthcare provider.
        In production, use real SMTP configuration.
        """
        print(f"📧 Sending email to {to_email}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        
        # Simulate email sending
        time.sleep(1)
        return True
    
    def _format_verification_email(self, request: VerificationRequest) -> str:
        """Format verification email for healthcare provider."""
        return f"""
🏥 EHR Clinical Data Verification Request

Dear Dr. {request.doctor_name},

We are conducting a routine audit of our Electronic Health Records system and have identified a potential inconsistency in the following patient's clinical data that requires your verification:

📋 Patient Information:
• Patient ID: {request.patient_id}
• Hospital: {request.hospital_name}
• Patient Consent: ✅ Obtained

🔍 Clinical Issue Identified:
{request.clinical_issue}

📝 Detailed Grievance:
{request.grievance_details.get('issue', 'No specific issue provided')}

⚕️ Required Action:
Please review the patient's records and confirm whether the above clinical information is accurate.

Reply Options:
• CONFIRM - The clinical information is correct
• CORRECT - The information needs correction (please provide details)
• CLARIFY - Need additional information before verification

🔒 Privacy Notice:
This verification is conducted with patient consent and complies with HIPAA regulations. 
Please respond within 48 hours to ensure timely record updates.

Thank you for your cooperation in maintaining accurate medical records.

Best regards,
EHR Quality Assurance Team
        """.strip()
    
    def create_verification_request(self, patient_data: Dict, grievance_details: Dict, patient_consent: bool) -> VerificationRequest:
        """Create a verification request for clinical issues."""
        
        request = VerificationRequest(
            patient_id=patient_data.get('Patient_ID', ''),
            doctor_name=patient_data.get('Doctor', ''),
            hospital_name=patient_data.get('Hospital', ''),
            email=self._generate_doctor_email(patient_data.get('Doctor', ''), patient_data.get('Hospital', '')),
            clinical_issue=grievance_details.get('issue', ''),
            patient_consent=patient_consent,
            grievance_details=grievance_details,
            created_at=time.time()
        )
        
        return request
    
    def _generate_doctor_email(self, doctor_name: str, hospital_name: str) -> str:
        """Generate realistic doctor email for demo purposes."""
        # Clean names for email generation
        doctor_clean = doctor_name.lower().replace(' ', '.').replace('.', '')
        hospital_clean = hospital_name.lower().replace(' ', '').replace(',', '').replace('.', '')
        
        # Generate email format
        email_formats = [
            f"{doctor_clean}@{hospital_clean}.com",
            f"{doctor_clean}@med.{hospital_clean}.com",
            f"dr.{doctor_clean}@{hospital_clean}.org",
        ]
        
        return email_formats[0]  # Return first format for consistency
    
    def send_verification_request(self, request: VerificationRequest) -> bool:
        """Send verification request to healthcare provider."""
        
        if not request.patient_consent:
            print(f"⚠️ Patient consent not obtained for {request.patient_id}, skipping verification")
            return False
        
        subject = f"EHR Verification Request - Patient {request.patient_id}"
        body = self._format_verification_email(request)
        
        # Send email
        if self._send_email(request.email, subject, body):
            self.verification_requests.append(request)
            print(f"✅ Verification request sent to Dr. {request.doctor_name} for Patient {request.patient_id}")
            return True
        else:
            print(f"❌ Failed to send verification request for Patient {request.patient_id}")
            return False
    
    def record_doctor_response(self, patient_id: str, response: str, status: VerificationStatus) -> bool:
        """Record doctor's response to verification request."""
        
        # Find the verification request
        request = None
        for req in self.verification_requests:
            if req.patient_id == patient_id and req.status == VerificationStatus.PENDING:
                request = req
                break
        
        if not request:
            print(f"❌ No pending verification request found for Patient {patient_id}")
            return False
        
        # Update request with response
        request.status = status
        request.response = response
        
        # Store response
        if patient_id not in self.responses:
            self.responses[patient_id] = []
        
        self.responses[patient_id].append({
            'response': response,
            'status': status.value,
            'timestamp': time.time(),
            'doctor': request.doctor_name,
            'hospital': request.hospital_name
        })
        
        print(f"📝 Recorded response from Dr. {request.doctor_name} for Patient {patient_id}")
        print(f"   Response: {response}")
        print(f"   Status: {status.value}")
        
        return True
    
    def get_verification_summary(self) -> Dict[str, Any]:
        """Get summary of verification process."""
        total_requests = len(self.verification_requests)
        pending = sum(1 for req in self.verification_requests if req.status == VerificationStatus.PENDING)
        confirmed = sum(1 for req in self.verification_requests if req.status == VerificationStatus.CONFIRMED)
        rejected = sum(1 for req in self.verification_requests if req.status == VerificationStatus.REJECTED)
        
        summary = {
            'total_verification_requests': total_requests,
            'pending_requests': pending,
            'confirmed_requests': confirmed,
            'rejected_requests': rejected,
            'response_rate': ((total_requests - pending) / total_requests * 100) if total_requests > 0 else 0,
            'verification_requests': [
                {
                    'patient_id': req.patient_id,
                    'doctor': req.doctor_name,
                    'hospital': req.hospital_name,
                    'status': req.status.value,
                    'created_at': req.created_at,
                    'response': req.response
                }
                for req in self.verification_requests
            ],
            'doctor_responses': self.responses
        }
        
        return summary


def main():
    """Demo function to test doctor verification."""
    verifier = DoctorVerifier()
    
    # Sample patient data with clinical issue
    sample_patient = {
        'Patient_ID': 'PID-000001',
        'Name': 'John Doe',
        'Doctor': 'Matthew Smith',
        'Hospital': 'Sons and Miller'
    }
    
    sample_grievance = {
        'issue': 'Diagnosis of Cancer in 30-year-old patient with no supporting lab evidence',
        'correction_needed': 'Require biopsy results and imaging studies to confirm diagnosis',
        'original_text': 'Full grievance report text...'
    }
    
    # Create and send verification request
    request = verifier.create_verification_request(
        sample_patient, 
        sample_grievance, 
        patient_consent=True
    )
    
    if verifier.send_verification_request(request):
        print("✅ Verification request sent successfully")
        
        # Simulate doctor response
        time.sleep(2)
        verifier.record_doctor_response(
            'PID-000001', 
            'CONFIRMED - Diagnosis verified with pathology report #12345', 
            VerificationStatus.CONFIRMED
        )
        
        # Show summary
        summary = verifier.get_verification_summary()
        print("\n📊 Verification Summary:")
        print(json.dumps(summary, indent=2))
    else:
        print("❌ Failed to send verification request")


if __name__ == "__main__":
    main()
