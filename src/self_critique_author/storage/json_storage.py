"""JSON file storage implementation."""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.grievance import GrievanceReport
from ..models.message import VerificationMessage
from ..utils.logger import get_logger


class JSONStorage:
    """JSON file storage for grievances and messages."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger("json_storage", config.get("logging", {}))
        
        # Create directories
        self.grievance_dir = Path(config.get("grievance_directory", "data/processed/grievances"))
        self.message_dir = Path(config.get("message_directory", "data/processed/messages"))
        self.output_dir = Path(config.get("output_directory", "data/processed"))
        
        self.grievance_dir.mkdir(parents=True, exist_ok=True)
        self.message_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def save_grievance(self, grievance: GrievanceReport) -> str:
        """Save grievance report to JSON file."""
        file_path = self.grievance_dir / f"{grievance.patient_id}_grievance.json"
        
        # Prepare data for saving
        grievance_data = grievance.to_dict()
        grievance_data["storage_metadata"] = {
            "saved_at": datetime.now().isoformat(),
            "storage_format": "json",
            "version": "2.0.0"
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(grievance_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(
                f"Grievance report saved",
                patient_id=grievance.patient_id,
                file_path=str(file_path),
                inconsistencies_count=grievance.total_inconsistencies
            )
            
            return str(file_path)
            
        except Exception as e:
            self.logger.error(
                f"Failed to save grievance report",
                patient_id=grievance.patient_id,
                error=str(e)
            )
            raise
    
    def load_grievance(self, patient_id: str) -> Optional[GrievanceReport]:
        """Load grievance report from JSON file."""
        file_path = self.grievance_dir / f"{patient_id}_grievance.json"
        
        if not file_path.exists():
            self.logger.warning(f"Grievance file not found", patient_id=patient_id)
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct grievance report
            grievance = GrievanceReport(
                patient_id=data["patient_id"],
                status=data["status"],
                total_inconsistencies=data["total_inconsistencies"],
                inconsistencies=[],  # Will be reconstructed from raw_report
                correction_needed=data["correction_needed"],
                audit_timestamp=datetime.fromisoformat(data["audit_timestamp"]),
                auditor_version=data.get("auditor_version", "2.0.0"),
                raw_report=data.get("raw_report"),
                processing_time_ms=data.get("processing_time_ms"),
                reviewer_comments=data.get("reviewer_comments")
            )
            
            # Reconstruct inconsistencies from raw report
            if grievance.raw_report:
                grievance.inconsistencies = GrievanceReport._parse_inconsistencies(grievance.raw_report)
            
            self.logger.info(
                f"Grievance report loaded",
                patient_id=patient_id,
                file_path=str(file_path)
            )
            
            return grievance
            
        except Exception as e:
            self.logger.error(
                f"Failed to load grievance report",
                patient_id=patient_id,
                error=str(e)
            )
            return None
    
    def save_message(self, message: VerificationMessage) -> str:
        """Save verification message to JSON file."""
        file_path = self.message_dir / f"{message.patient_id}_messages.json"
        
        try:
            # Load existing data if file exists
            existing_data = {"messages": [], "responses": [], "patient_info": {}}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Add new message
            message_data = message.to_dict()
            message_data["storage_metadata"] = {
                "saved_at": datetime.now().isoformat(),
                "storage_format": "json",
                "version": "2.0.0"
            }
            
            existing_data["messages"].append(message_data)
            
            # Save updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(
                f"Message saved",
                patient_id=message.patient_id,
                message_type=message.message_type.value,
                status=message.status.value
            )
            
            return str(file_path)
            
        except Exception as e:
            self.logger.error(
                f"Failed to save message",
                patient_id=message.patient_id,
                error=str(e)
            )
            raise
    
    def save_message_response(self, patient_id: str, response_data: Dict[str, Any]) -> str:
        """Save message response to JSON file."""
        file_path = self.message_dir / f"{patient_id}_messages.json"
        
        try:
            # Load existing data if file exists
            existing_data = {"messages": [], "responses": [], "patient_info": {}}
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Add response
            response_data["storage_metadata"] = {
                "saved_at": datetime.now().isoformat(),
                "storage_format": "json",
                "version": "2.0.0"
            }
            
            existing_data["responses"].append(response_data)
            
            # Save updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(
                f"Message response saved",
                patient_id=patient_id,
                response=response_data.get("response", "unknown")
            )
            
            return str(file_path)
            
        except Exception as e:
            self.logger.error(
                f"Failed to save message response",
                patient_id=patient_id,
                error=str(e)
            )
            raise
    
    def get_all_grievances(self) -> List[GrievanceReport]:
        """Get all grievance reports."""
        grievances = []
        
        for file_path in self.grievance_dir.glob("*_grievance.json"):
            patient_id = file_path.stem.replace("_grievance", "")
            grievance = self.load_grievance(patient_id)
            if grievance:
                grievances.append(grievance)
        
        return grievances
    
    def get_all_messages(self, patient_id: str) -> List[VerificationMessage]:
        """Get all messages for a patient."""
        file_path = self.message_dir / f"{patient_id}_messages.json"
        
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            messages = []
            for msg_data in data.get("messages", []):
                # Reconstruct message
                message = VerificationMessage(
                    patient_id=msg_data["patient_id"],
                    message_type=MessageType(msg_data["message_type"]),
                    recipient=msg_data["recipient"],
                    content=msg_data["content"],
                    options=msg_data["options"],
                    created_at=datetime.fromisoformat(msg_data["created_at"])
                )
                
                # Set optional fields
                if msg_data.get("sent_at"):
                    message.sent_at = datetime.fromisoformat(msg_data["sent_at"])
                if msg_data.get("response"):
                    message.response = msg_data["response"]
                    message.response_type = ResponseType(msg_data["response_type"])
                    message.responded_at = datetime.fromisoformat(msg_data["responded_at"])
                
                messages.append(message)
            
            return messages
            
        except Exception as e:
            self.logger.error(
                f"Failed to load messages",
                patient_id=patient_id,
                error=str(e)
            )
            return []
    
    def get_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """Get complete summary for a patient."""
        grievance = self.load_grievance(patient_id)
        messages = self.get_all_messages(patient_id)
        
        summary = {
            "patient_id": patient_id,
            "grievance": grievance.to_dict() if grievance else None,
            "messages": [msg.to_dict() for msg in messages],
            "message_count": len(messages),
            "responded": any(msg.response for msg in messages),
            "last_activity": None
        }
        
        # Find last activity
        timestamps = []
        if grievance:
            timestamps.append(grievance.audit_timestamp)
        
        for msg in messages:
            timestamps.append(msg.created_at)
            if msg.responded_at:
                timestamps.append(msg.responded_at)
        
        if timestamps:
            summary["last_activity"] = max(timestamps).isoformat()
        
        return summary
    
    def create_summary_report(self) -> Dict[str, Any]:
        """Create summary report of all stored data."""
        grievances = self.get_all_grievances()
        
        total_patients = len(grievances)
        inconsistent_patients = len([g for g in grievances if g.status == "Not Consistent"])
        total_inconsistencies = sum(g.total_inconsistencies for g in grievances)
        
        # Count by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for grievance in grievances:
            for inc in grievance.inconsistencies:
                severity_counts[inc.severity.value] += 1
        
        # Message statistics
        all_message_files = list(self.message_dir.glob("*_messages.json"))
        total_messages = 0
        total_responses = 0
        
        for file_path in all_message_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                total_messages += len(data.get("messages", []))
                total_responses += len(data.get("responses", []))
            except:
                continue
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "storage_format": "json",
            "version": "2.0.0",
            "patient_statistics": {
                "total_patients": total_patients,
                "inconsistent_patients": inconsistent_patients,
                "consistency_rate": (total_patients - inconsistent_patients) / total_patients if total_patients > 0 else 0
            },
            "grievance_statistics": {
                "total_inconsistencies": total_inconsistencies,
                "severity_breakdown": severity_counts,
                "average_inconsistencies_per_patient": total_inconsistencies / total_patients if total_patients > 0 else 0
            },
            "message_statistics": {
                "total_messages": total_messages,
                "total_responses": total_responses,
                "response_rate": total_responses / total_messages if total_messages > 0 else 0
            },
            "storage_locations": {
                "grievance_directory": str(self.grievance_dir),
                "message_directory": str(self.message_dir),
                "output_directory": str(self.output_dir)
            }
        }
        
        # Save summary report
        summary_path = self.output_dir / "storage_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(
            f"Storage summary report created",
            file_path=str(summary_path),
            total_patients=total_patients,
            total_inconsistencies=total_inconsistencies
        )
        
        return summary
