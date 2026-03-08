"""Data validation utilities."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re

from ..models.patient import PatientRecord


class DataValidator:
    """Data validation utilities for patient records."""
    
    def __init__(self, config):
        self.config = config
        self.required_fields = config.validation.get("required_fields", [])
        self.age_range = config.validation.get("age_range", {"min": 0, "max": 150})
        self.phone_format = config.validation.get("phone_format", "international")
        self.strict_mode = config.validation.get("strict_mode", False)
    
    def validate_patient_record(self, patient: PatientRecord) -> Dict[str, Any]:
        """Validate a complete patient record."""
        errors = []
        warnings = []
        
        # Check required fields
        for field in self.required_fields:
            if not hasattr(patient, field) or not getattr(patient, field):
                errors.append(f"Missing required field: {field}")
        
        # Validate age
        age_validation = self._validate_age(patient.age)
        errors.extend(age_validation["errors"])
        warnings.extend(age_validation["warnings"])
        
        # Validate phone number
        phone_validation = self._validate_phone_number(patient.cell_number)
        errors.extend(phone_validation["errors"])
        warnings.extend(phone_validation["warnings"])
        
        # Validate dates
        date_fields = {
            "date_of_admission": patient.date_of_admission,
            "discharge_date": patient.discharge_date,
            "date_of_birth": patient.date_of_birth
        }
        
        for field_name, date_value in date_fields.items():
            if date_value:
                date_validation = self._validate_date(date_value, field_name)
                errors.extend(date_validation["errors"])
                warnings.extend(date_validation["warnings"])
        
        # Validate age-DOB consistency
        if patient.age and patient.date_of_birth:
            consistency_validation = self._validate_age_dob_consistency(patient.age, patient.date_of_birth)
            errors.extend(consistency_validation["errors"])
            warnings.extend(consistency_validation["warnings"])
        
        # Validate admission-discharge date logic
        if patient.date_of_admission and patient.discharge_date:
            date_logic_validation = self._validate_admission_discharge_logic(patient.date_of_admission, patient.discharge_date)
            errors.extend(date_logic_validation["errors"])
            warnings.extend(date_logic_validation["warnings"])
        
        # Validate name format
        name_validation = self._validate_name_format(patient.name)
        errors.extend(name_validation["errors"])
        warnings.extend(name_validation["warnings"])
        
        # Validate medical data
        medical_validation = self._validate_medical_data(patient)
        errors.extend(medical_validation["errors"])
        warnings.extend(medical_validation["warnings"])
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "strict_mode": self.strict_mode
        }
    
    def _validate_age(self, age: int) -> Dict[str, List[str]]:
        """Validate patient age."""
        errors = []
        warnings = []
        
        if not isinstance(age, int):
            errors.append("Age must be an integer")
            return {"errors": errors, "warnings": warnings}
        
        if age < self.age_range["min"] or age > self.age_range["max"]:
            warnings.append(f"Unusual age: {age} (expected range: {self.age_range['min']}-{self.age_range['max']})")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_phone_number(self, phone: str) -> Dict[str, List[str]]:
        """Validate phone number format."""
        errors = []
        warnings = []
        
        if not phone:
            if "cell_number" in self.required_fields:
                errors.append("Phone number is required")
            return {"errors": errors, "warnings": warnings}
        
        if self.phone_format == "international":
            # Should start with +
            if not phone.startswith('+'):
                warnings.append(f"Phone number should include country code: {phone}")
            
            # Basic international format validation
            if not re.match(r'^\+\d{1,3}\d{3,15}$', phone.replace('-', '').replace(' ', '')):
                warnings.append(f"Phone number format may be invalid: {phone}")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_date(self, date_str: str, field_name: str) -> Dict[str, List[str]]:
        """Validate date format."""
        errors = []
        warnings = []
        
        if not date_str:
            return {"errors": errors, "warnings": warnings}
        
        # Try common date formats
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"]
        parsed_date = None
        
        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            errors.append(f"Invalid date format for {field_name}: {date_str}")
        else:
            # Check for reasonable date ranges
            year = parsed_date.year
            if year < 1900 or year > datetime.now().year + 1:
                warnings.append(f"Unusual year in {field_name}: {year}")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_age_dob_consistency(self, age: int, date_of_birth: str) -> Dict[str, List[str]]:
        """Validate consistency between age and date of birth."""
        errors = []
        warnings = []
        
        try:
            # Extract year from DOB
            if "-" in date_of_birth:
                birth_year = int(date_of_birth.split("-")[-1])
            elif "/" in date_of_birth:
                birth_year = int(date_of_birth.split("/")[-1])
            else:
                return {"errors": errors, "warnings": warnings}
            
            # Calculate expected age (assuming current year is 2026)
            current_year = datetime.now().year
            expected_age = current_year - birth_year
            
            # Allow 1 year tolerance
            if abs(age - expected_age) > 1:
                warnings.append(f"Age-DOB inconsistency: Age {age} vs DOB {date_of_birth} (expected ~{expected_age})")
            
        except ValueError:
            warnings.append(f"Could not parse date of birth: {date_of_birth}")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_admission_discharge_logic(self, admission_date: str, discharge_date: str) -> Dict[str, List[str]]:
        """Validate admission and discharge date logic."""
        errors = []
        warnings = []
        
        try:
            # Parse dates
            formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]
            adm_date = None
            dis_date = None
            
            for fmt in formats:
                try:
                    adm_date = datetime.strptime(admission_date, fmt)
                    break
                except ValueError:
                    continue
            
            for fmt in formats:
                try:
                    dis_date = datetime.strptime(discharge_date, fmt)
                    break
                except ValueError:
                    continue
            
            if adm_date and dis_date:
                if dis_date < adm_date:
                    errors.append(f"Discharge date {discharge_date} is before admission date {admission_date}")
                
                # Check for unusually long stays
                stay_duration = (dis_date - adm_date).days
                if stay_duration > 365:
                    warnings.append(f"Unusually long hospital stay: {stay_duration} days")
        
        except Exception:
            warnings.append("Could not validate admission/discharge date logic")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_name_format(self, name: str) -> Dict[str, List[str]]:
        """Validate name format."""
        errors = []
        warnings = []
        
        if not name:
            errors.append("Name is required")
            return {"errors": errors, "warnings": warnings}
        
        # Check for proper capitalization
        words = name.split()
        for word in words:
            if word and not word[0].isupper():
                warnings.append(f"Name capitalization issue: '{word}' should start with capital letter")
        
        # Check for unusual characters
        if re.search(r'[0-9@#$%^&*()_+=\[\]{}|\\:";\'<>?,./]', name):
            warnings.append(f"Name contains unusual characters: {name}")
        
        # Check length
        if len(name) < 2:
            errors.append("Name is too short")
        elif len(name) > 100:
            warnings.append(f"Name is unusually long: {len(name)} characters")
        
        return {"errors": errors, "warnings": warnings}
    
    def _validate_medical_data(self, patient: PatientRecord) -> Dict[str, List[str]]:
        """Validate medical data fields."""
        errors = []
        warnings = []
        
        # Validate blood type
        valid_blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        if patient.blood_type and patient.blood_type not in valid_blood_types:
            warnings.append(f"Unusual blood type: {patient.blood_type}")
        
        # Validate gender
        valid_genders = ["Male", "Female", "Other"]
        if patient.gender and patient.gender not in valid_genders:
            warnings.append(f"Unusual gender: {patient.gender}")
        
        # Validate admission type
        valid_admission_types = ["Elective", "Urgent", "Emergency"]
        if patient.admission_type and patient.admission_type not in valid_admission_types:
            warnings.append(f"Unusual admission type: {patient.admission_type}")
        
        # Validate test results
        valid_test_results = ["Normal", "Abnormal", "Inconclusive", "Pending"]
        if patient.test_results and patient.test_results not in valid_test_results:
            warnings.append(f"Unusual test result: {patient.test_results}")
        
        # Validate billing amount
        if patient.billing_amount:
            if patient.billing_amount < 0:
                errors.append("Billing amount cannot be negative")
            elif patient.billing_amount > 1000000:
                warnings.append(f"Unusually high billing amount: ${patient.billing_amount:,.2f}")
        
        # Validate room number
        if patient.room_number:
            if patient.room_number < 1 or patient.room_number > 9999:
                warnings.append(f"Unusual room number: {patient.room_number}")
        
        # Validate weight and height
        if patient.weight:
            if patient.weight < 1 or patient.weight > 500:
                warnings.append(f"Unusual weight: {patient.weight} kg")
        
        if patient.height:
            if patient.height < 50 or patient.height > 250:
                warnings.append(f"Unusual height: {patient.height} cm")
        
        # Calculate BMI validation
        if patient.weight > 0 and patient.height > 0:
            bmi = patient.weight / ((patient.height / 100) ** 2)
            if bmi < 10 or bmi > 70:
                warnings.append(f"Unusual BMI: {bmi:.1f}")
        
        return {"errors": errors, "warnings": warnings}
    
    def validate_batch(self, patients: List[PatientRecord]) -> Dict[str, Any]:
        """Validate a batch of patient records."""
        results = []
        total_errors = 0
        total_warnings = 0
        
        for patient in patients:
            validation_result = self.validate_patient_record(patient)
            results.append({
                "patient_id": patient.patient_id,
                "validation": validation_result
            })
            total_errors += len(validation_result["errors"])
            total_warnings += len(validation_result["warnings"])
        
        return {
            "total_patients": len(patients),
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "results": results,
            "batch_valid": total_errors == 0
        }
