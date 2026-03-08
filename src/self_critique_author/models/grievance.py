"""Data models for grievance reports."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class GrievanceType(Enum):
    """Type of grievance."""
    USER_DATA = "user_data"
    CLINICAL_DATA = "clinical_data"
    TEMPORAL = "temporal"
    FORMAT = "format"


class GrievanceSeverity(Enum):
    """Severity level of grievance."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Inconsistency:
    """Individual inconsistency found in audit."""
    
    description: str
    field_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    severity: GrievanceSeverity = GrievanceSeverity.MEDIUM
    category: GrievanceType = GrievanceType.USER_DATA
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "description": self.description,
            "field_name": self.field_name,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "severity": self.severity.value,
            "category": self.category.value
        }


@dataclass
class GrievanceReport:
    """Complete grievance report for a patient."""
    
    patient_id: str
    status: str  # "Consistent" or "Not Consistent"
    total_inconsistencies: int
    inconsistencies: List[Inconsistency]
    correction_needed: str
    audit_timestamp: datetime
    auditor_version: str = "2.0.0"
    
    # Raw report text (from LLM)
    raw_report: Optional[str] = None
    
    # Metadata
    processing_time_ms: Optional[int] = None
    reviewer_comments: Optional[str] = None
    
    @classmethod
    def from_cove_format(cls, patient_id: str, raw_report: str, 
                         processing_time_ms: Optional[int] = None) -> "GrievanceReport":
        """Create grievance report from CoVE format text."""
        
        # Parse status
        status = "Consistent"
        if "STATUS: NOT CONSISTENT" in raw_report.upper():
            status = "Not Consistent"
        
        # Parse total inconsistencies
        total_inconsistencies = 0
        for line in raw_report.split('\n'):
            if 'TOTAL INCONSISTENCIES FOUND:' in line:
                try:
                    count_part = line.split(':')[1].strip()
                    total_inconsistencies = int(count_part.split()[0])
                except:
                    pass
                break
        
        # Parse inconsistencies from CoVE process
        inconsistencies = cls._parse_inconsistencies(raw_report)
        
        # Extract correction needed section
        correction_needed = ""
        if "CORRECTION NEEDED:" in raw_report:
            correction_section = raw_report.split("CORRECTION NEEDED:")[1].strip()
            correction_needed = correction_section
        
        return cls(
            patient_id=patient_id,
            status=status,
            total_inconsistencies=total_inconsistencies,
            inconsistencies=inconsistencies,
            correction_needed=correction_needed,
            audit_timestamp=datetime.now(),
            raw_report=raw_report,
            processing_time_ms=processing_time_ms
        )
    
    @staticmethod
    def _parse_inconsistencies(raw_report: str) -> List[Inconsistency]:
        """Parse inconsistencies from CoVE format report."""
        inconsistencies = []
        
        # Look for CoVE process section
        if "CHAIN OF VERIFICATION (CoVE) PROCESS:" in raw_report:
            cove_section = raw_report.split("CHAIN OF VERIFICATION (CoVE) PROCESS:")[1]
            
            # Split by numbered items
            lines = cove_section.split('\n')
            current_inconsistency = ""
            
            for line in lines:
                line = line.strip()
                
                # Stop at correction section
                if line.startswith("CORRECTION NEEDED:"):
                    break
                
                # Check if line starts with number
                if line and line[0].isdigit() and '.' in line[:5]:
                    # Save previous inconsistency
                    if current_inconsistency.strip():
                        inconsistency = cls._parse_single_inconsistency(current_inconsistency.strip())
                        if inconsistency:
                            inconsistencies.append(inconsistency)
                    current_inconsistency = line
                else:
                    # Continue current inconsistency
                    current_inconsistency += ' ' + line
            
            # Add last inconsistency
            if current_inconsistency.strip():
                inconsistency = cls._parse_single_inconsistency(current_inconsistency.strip())
                if inconsistency:
                    inconsistencies.append(inconsistency)
        
        return inconsistencies
    
    @staticmethod
    def _parse_single_inconsistency(text: str) -> Optional[Inconsistency]:
        """Parse a single inconsistency from text."""
        # Remove numbering
        if text and text[0].isdigit():
            parts = text.split('.', 1)
            if len(parts) > 1:
                text = parts[1].strip()
        
        if not text or len(text) < 10:
            return None
        
        # Determine category and severity based on keywords
        category = GrievanceType.USER_DATA
        severity = GrievanceSeverity.MEDIUM
        
        text_lower = text.lower()
        
        # Clinical indicators
        if any(keyword in text_lower for keyword in ['diagnosis', 'treatment', 'medication', 'clinical']):
            category = GrievanceType.CLINICAL_DATA
            severity = GrievanceSeverity.HIGH
        
        # Temporal indicators
        if any(keyword in text_lower for keyword in ['date', 'age', 'time', 'admission', 'discharge']):
            category = GrievanceType.TEMPORAL
            severity = GrievanceSeverity.HIGH
        
        # Format indicators
        if any(keyword in text_lower for keyword in ['format', 'capitalization', 'case', 'spelling']):
            category = GrievanceType.FORMAT
            severity = GrievanceSeverity.LOW
        
        # Critical indicators
        if any(keyword in text_lower for keyword in ['missing', 'invalid', 'critical', 'emergency']):
            severity = GrievanceSeverity.CRITICAL
        
        return Inconsistency(
            description=text,
            category=category,
            severity=severity
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "patient_id": self.patient_id,
            "status": self.status,
            "total_inconsistencies": self.total_inconsistencies,
            "inconsistencies": [inc.to_dict() for inc in self.inconsistencies],
            "correction_needed": self.correction_needed,
            "audit_timestamp": self.audit_timestamp.isoformat(),
            "auditor_version": self.auditor_version,
            "raw_report": self.raw_report,
            "processing_time_ms": self.processing_time_ms,
            "reviewer_comments": self.reviewer_comments
        }
    
    def get_summary(self) -> str:
        """Get summary of grievance report."""
        if self.status == "Consistent":
            return "No inconsistencies found"
        
        severity_counts = {}
        for inc in self.inconsistencies:
            severity = inc.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        summary_parts = []
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{count} {severity}")
        
        return f"{self.total_inconsistencies} issues: {', '.join(summary_parts)}"
    
    def get_user_data_inconsistencies(self) -> List[Inconsistency]:
        """Get only user data inconsistencies."""
        return [inc for inc in self.inconsistencies if inc.category == GrievanceType.USER_DATA]
    
    def get_clinical_inconsistencies(self) -> List[Inconsistency]:
        """Get only clinical inconsistencies."""
        return [inc for inc in self.inconsistencies if inc.category == GrievanceType.CLINICAL_DATA]
    
    def has_critical_issues(self) -> bool:
        """Check if report has critical issues."""
        return any(inc.severity == GrievanceSeverity.CRITICAL for inc in self.inconsistencies)
    
    def add_reviewer_comment(self, comment: str):
        """Add reviewer comment."""
        self.reviewer_comments = comment
