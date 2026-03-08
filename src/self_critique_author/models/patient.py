"""Data models for patient records."""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class PatientRecord:
    """Patient record data model."""
    
    # Basic demographics
    name: str
    age: int
    gender: str
    blood_type: str
    medical_condition: str
    date_of_admission: str
    doctor: str
    hospital: str
    insurance_provider: str
    
    # Clinical data
    billing_amount: float
    room_number: int
    admission_type: str
    discharge_date: str
    medication: str
    test_results: str
    
    # Identifiers
    patient_id: str
    date_of_birth: str
    weight: float
    height: float
    cell_number: str
    
    # Audit fields
    consistent_or_not: Optional[str] = None
    grievance_report: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatientRecord":
        """Create patient record from dictionary."""
        # Handle type conversions
        billing_amount = float(data.get("Billing Amount", 0))
        room_number = int(data.get("Room Number", 0))
        weight = float(data.get("Weight", 0))
        height = float(data.get("Height", 0))
        
        return cls(
            name=data.get("Name", ""),
            age=int(data.get("Age", 0)),
            gender=data.get("Gender", ""),
            blood_type=data.get("Blood Type", ""),
            medical_condition=data.get("Medical Condition", ""),
            date_of_admission=data.get("Date of Admission", ""),
            doctor=data.get("Doctor", ""),
            hospital=data.get("Hospital", ""),
            insurance_provider=data.get("Insurance Provider", ""),
            billing_amount=billing_amount,
            room_number=room_number,
            admission_type=data.get("Admission Type", ""),
            discharge_date=data.get("Discharge Date", ""),
            medication=data.get("Medication", ""),
            test_results=data.get("Test Results", ""),
            patient_id=data.get("Patient_ID", ""),
            date_of_birth=data.get("Date_of_Birth", ""),
            weight=weight,
            height=height,
            cell_number=data.get("cell_number", ""),
            consistent_or_not=data.get("Consistent_or_Not"),
            grievance_report=data.get("Grievance_Report")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert patient record to dictionary."""
        return {
            "Name": self.name,
            "Age": self.age,
            "Gender": self.gender,
            "Blood Type": self.blood_type,
            "Medical Condition": self.medical_condition,
            "Date of Admission": self.date_of_admission,
            "Doctor": self.doctor,
            "Hospital": self.hospital,
            "Insurance Provider": self.insurance_provider,
            "Billing Amount": self.billing_amount,
            "Room Number": self.room_number,
            "Admission Type": self.admission_type,
            "Discharge Date": self.discharge_date,
            "Medication": self.medication,
            "Test Results": self.test_results,
            "Patient_ID": self.patient_id,
            "Date_of_Birth": self.date_of_birth,
            "Weight": self.weight,
            "Height": self.height,
            "cell_number": self.cell_number,
            "Consistent_or_Not": self.consistent_or_not,
            "Grievance_Report": self.grievance_report
        }
    
    def validate(self) -> Dict[str, Any]:
        """Validate patient record data."""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = [
            "name", "age", "gender", "patient_id", "date_of_birth"
        ]
        
        for field in required_fields:
            if not getattr(self, field, None):
                errors.append(f"Missing required field: {field}")
        
        # Age validation
        if self.age < 0 or self.age > 150:
            warnings.append(f"Unusual age: {self.age}")
        
        # Phone number validation
        if self.cell_number and not self.cell_number.startswith('+'):
            warnings.append(f"Phone number should include country code: {self.cell_number}")
        
        # Date format validation
        date_fields = ["date_of_admission", "discharge_date", "date_of_birth"]
        for field in date_fields:
            date_str = getattr(self, field, "")
            if date_str and not self._is_valid_date(date_str):
                warnings.append(f"Invalid date format for {field}: {date_str}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is in valid format."""
        try:
            # Try common date formats
            formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]
            for fmt in formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except:
            return False
    
    def get_display_name(self) -> str:
        """Get formatted display name."""
        if self.name:
            return self.name.title()
        return f"Patient {self.patient_id}"
    
    def get_age_dob_consistency(self) -> bool:
        """Check if age is consistent with date of birth."""
        try:
            # Extract year from DOB
            if "-" in self.date_of_birth:
                birth_year = int(self.date_of_birth.split("-")[-1])
            elif "/" in self.date_of_birth:
                birth_year = int(self.date_of_birth.split("/")[-1])
            else:
                return False
            
            # Calculate expected age (assuming current year is 2026)
            expected_age = 2026 - birth_year
            
            # Allow 1 year tolerance
            return abs(self.age - expected_age) <= 1
        except:
            return False
