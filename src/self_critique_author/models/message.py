"""Data models for verification messages."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class MessageType(Enum):
    """Type of verification message."""
    USER_DATA_VERIFICATION = "user_data_verification"
    CLINICAL_DATA_VERIFICATION = "clinical_data_verification"
    FOLLOW_UP = "follow_up"
    CONFIRMATION = "confirmation"


class MessageStatus(Enum):
    """Status of message."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    FAILED = "failed"


class ResponseType(Enum):
    """Type of response."""
    YES = "yes"
    NO = "no"
    DETAILS = "details"
    CONFIRM = "confirm"
    DECLINE = "decline"
    CORRECT = "correct"
    CLARIFY = "clarify"


@dataclass
class VerificationMessage:
    """Verification message data model."""
    
    patient_id: str
    message_type: MessageType
    recipient: str  # Phone number or email
    content: str
    options: List[str]
    
    # Timestamps
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    # Status tracking
    status: MessageStatus = MessageStatus.PENDING
    delivery_attempts: int = 0
    last_error: Optional[str] = None
    
    # Response data
    response: Optional[str] = None
    response_type: Optional[ResponseType] = None
    responded_at: Optional[datetime] = None
    
    # Metadata
    grievance_data: Optional[Dict[str, Any]] = None
    template_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patient_id": self.patient_id,
            "message_type": self.message_type.value,
            "recipient": self.recipient,
            "content": self.content,
            "options": self.options,
            "created_at": self.created_at.isoformat(),
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "status": self.status.value,
            "delivery_attempts": self.delivery_attempts,
            "last_error": self.last_error,
            "response": self.response,
            "response_type": self.response_type.value if self.response_type else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
            "grievance_data": self.grievance_data,
            "template_used": self.template_used
        }
    
    def mark_sent(self):
        """Mark message as sent."""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.now()
        self.delivery_attempts += 1
    
    def mark_delivered(self):
        """Mark message as delivered."""
        self.status = MessageStatus.DELIVERED
        self.delivered_at = datetime.now()
    
    def mark_read(self):
        """Mark message as read."""
        self.status = MessageStatus.READ
        self.read_at = datetime.now()
    
    def record_response(self, response: str, response_type: ResponseType):
        """Record patient response."""
        self.response = response
        self.response_type = response_type
        self.responded_at = datetime.now()
        self.status = MessageStatus.RESPONDED
    
    def mark_failed(self, error: str):
        """Mark message as failed."""
        self.status = MessageStatus.FAILED
        self.last_error = error
        self.delivery_attempts += 1
    
    def get_age_minutes(self) -> int:
        """Get message age in minutes."""
        now = datetime.now()
        delta = now - self.created_at
        return int(delta.total_seconds() / 60)
    
    def is_expired(self, max_age_minutes: int = 1440) -> bool:
        """Check if message is expired (default 24 hours)."""
        return self.get_age_minutes() > max_age_minutes
    
    def needs_retry(self, max_attempts: int = 3) -> bool:
        """Check if message needs retry."""
        return (self.status == MessageStatus.FAILED and 
                self.delivery_attempts < max_attempts)


@dataclass
class MessageTemplate:
    """Message template for different types."""
    
    name: str
    message_type: MessageType
    subject_template: Optional[str] = None
    body_template: str = ""
    options: List[str] = None
    variables: List[str] = None
    
    def __post_init__(self):
        if self.options is None:
            self.options = []
        if self.variables is None:
            self.variables = []
    
    def render(self, variables: Dict[str, Any]) -> Dict[str, str]:
        """Render template with variables."""
        rendered = {
            "subject": "",
            "body": self.body_template,
            "options": self.options.copy()
        }
        
        # Render subject if present
        if self.subject_template:
            rendered["subject"] = self.subject_template.format(**variables)
        
        # Render body
        rendered["body"] = self.body_template.format(**variables)
        
        return rendered


# Standard message templates
USER_DATA_VERIFICATION_TEMPLATE = MessageTemplate(
    name="user_data_verification",
    message_type=MessageType.USER_DATA_VERIFICATION,
    body_template="""🏥 EHR Data Verification Required

Dear {patient_name},

We found some inconsistencies in your medical records that need verification:

{issues_summary}

❓ Please confirm:
{question}

Reply with:
• YES - If the information is correct
• NO - If the information is incorrect  
• DETAILS - To provide additional information

Thank you for helping us maintain accurate records.""",
    options=["YES", "NO", "DETAILS"],
    variables=["patient_name", "issues_summary", "question"]
)

CLINICAL_DATA_VERIFICATION_TEMPLATE = MessageTemplate(
    name="clinical_data_verification",
    message_type=MessageType.CLINICAL_DATA_VERIFICATION,
    body_template="""🏥 Clinical Record Verification Required

Dear {patient_name},

Our audit system found potential issues in your diagnosis/treatment records that require verification from your healthcare provider.

{issues_summary}

⚠️ This requires verification from your doctor/hospital.

Reply with:
• CONFIRM - To authorize us to contact your healthcare provider
• DECLINE - If you prefer not to proceed with verification
• DETAILS - To provide additional context

Your privacy is our priority. No information will be shared without your consent.""",
    options=["CONFIRM", "DECLINE", "DETAILS"],
    variables=["patient_name", "issues_summary"]
)

DOCTOR_VERIFICATION_TEMPLATE = MessageTemplate(
    name="doctor_verification",
    message_type=MessageType.CLINICAL_DATA_VERIFICATION,
    subject_template="EHR Verification Request - Patient {patient_id}",
    body_template="""🏥 EHR Clinical Data Verification Request

Dear Dr. {doctor_name},

We are conducting a routine audit of our Electronic Health Records system and have identified a potential inconsistency in the following patient's clinical data that requires your verification:

📋 Patient Information:
• Patient ID: {patient_id}
• Hospital: {hospital}
• Patient Consent: ✅ Obtained

🔍 Clinical Issue Identified:
{clinical_issue}

📝 Detailed Grievance:
{detailed_grievance}

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
EHR Quality Assurance Team""",
    options=["CONFIRM", "CORRECT", "CLARIFY"],
    variables=["doctor_name", "patient_id", "hospital", "clinical_issue", "detailed_grievance"]
)
