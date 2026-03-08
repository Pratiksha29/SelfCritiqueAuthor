"""Main pipeline orchestrator for EHR audit and verification."""

import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..utils.config import Config
from ..utils.logger import get_logger
from ..utils.validators import DataValidator
from ..models.patient import PatientRecord
from ..models.grievance import GrievanceReport
from ..storage.json_storage import JSONStorage
from .auditor import EHRAuditor
from .resolver import EHRResolver
from ..verification.whatsapp_verifier import WhatsAppVerifier
from ..verification.doctor_verifier import DoctorVerifier


class EHRPipeline:
    """Main pipeline for EHR audit and verification process."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = get_logger("pipeline", self.config.logging.__dict__)
        
        # Initialize components
        self.storage = JSONStorage(self.config.storage.__dict__)
        self.auditor = EHRAuditor(self.config)
        self.resolver = EHRResolver(self.config)
        self.whatsapp_verifier = WhatsAppVerifier(self.config) if self.config.verification.whatsapp_enabled else None
        self.doctor_verifier = DoctorVerifier(self.config) if self.config.verification.doctor_enabled else None
        self.validator = DataValidator(self.config)
        
        self.logger.info("EHR Pipeline initialized", version=self.config.app.version)
    
    def run(self, input_data_path: str, demo_mode: bool = False, demo_count: int = 5) -> Dict[str, Any]:
        """Run the complete EHR audit pipeline."""
        start_time = time.time()
        
        # Load input data
        patient_records = self._load_patient_data(input_data_path, demo_mode, demo_count)
        
        self.logger.log_pipeline_start(len(patient_records))
        
        # Step 1: Audit patient records
        grievances = self._run_audit_step(patient_records)
        
        # Step 2: Verification (if enabled)
        verification_results = self._run_verification_step(grievances) if self._should_run_verification() else {}
        
        # Step 3: Data resolution
        corrected_records = self._run_resolution_step(patient_records, grievances)
        
        # Step 4: Save results
        output_paths = self._save_results(corrected_records, grievances)
        
        # Generate summary
        processing_time_ms = int((time.time() - start_time) * 1000)
        summary = self._generate_summary(patient_records, grievances, verification_results, processing_time_ms)
        
        self.logger.log_pipeline_complete(len(patient_records), processing_time_ms)
        
        return {
            "summary": summary,
            "output_paths": output_paths,
            "processing_time_ms": processing_time_ms
        }
    
    def run_step(self, step: str, input_data_path: str, **kwargs) -> Dict[str, Any]:
        """Run a specific pipeline step."""
        step = step.lower()
        
        if step == "audit":
            return self._run_audit_only(input_data_path, **kwargs)
        elif step == "verify":
            return self._run_verification_only(**kwargs)
        elif step == "resolve":
            return self._run_resolution_only(input_data_path, **kwargs)
        else:
            raise ValueError(f"Unknown step: {step}")
    
    def _load_patient_data(self, input_path: str, demo_mode: bool, demo_count: int) -> List[PatientRecord]:
        """Load patient data from file."""
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if input_path.suffix == '.json':
            return self._load_json_data(input_path, demo_mode, demo_count)
        elif input_path.suffix == '.csv':
            return self._load_csv_data(input_path, demo_mode, demo_count)
        else:
            raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    def _load_json_data(self, input_path: Path, demo_mode: bool, demo_count: int) -> List[PatientRecord]:
        """Load patient data from JSON file."""
        import json
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if demo_mode:
            data = data[:demo_count]
        
        records = []
        for item in data:
            try:
                patient = PatientRecord.from_dict(item)
                
                # Validate record
                validation_result = patient.validate()
                if not validation_result["valid"]:
                    self.logger.warning(
                        f"Patient record validation failed",
                        patient_id=patient.patient_id,
                        errors=validation_result["errors"]
                    )
                
                records.append(patient)
                
            except Exception as e:
                self.logger.error(
                    f"Failed to load patient record",
                    error=str(e),
                    data=item.get("Patient_ID", "unknown")
                )
        
        self.logger.info(
            f"Patient data loaded from JSON",
            file_path=str(input_path),
            total_records=len(records)
        )
        
        return records
    
    def _load_csv_data(self, input_path: Path, demo_mode: bool, demo_count: int) -> List[PatientRecord]:
        """Load patient data from CSV file."""
        import pandas as pd
        
        df = pd.read_csv(input_path)
        
        if demo_mode:
            df = df.head(demo_count)
        
        records = []
        for _, row in df.iterrows():
            try:
                patient = PatientRecord.from_dict(row.to_dict())
                records.append(patient)
            except Exception as e:
                self.logger.error(
                    f"Failed to load patient record from CSV",
                    error=str(e),
                    patient_id=row.get("Patient_ID", "unknown")
                )
        
        self.logger.info(
            f"Patient data loaded from CSV",
            file_path=str(input_path),
            total_records=len(records)
        )
        
        return records
    
    def _run_audit_step(self, patient_records: List[PatientRecord]) -> List[GrievanceReport]:
        """Run audit step on patient records."""
        self.logger.info("Starting audit step")
        
        grievances = []
        for i, patient in enumerate(patient_records, 1):
            start_time = time.time()
            
            try:
                grievance = self.auditor.audit_patient_record(patient)
                grievances.append(grievance)
                
                # Save grievance
                self.storage.save_grievance(grievance)
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                self.logger.log_patient_processing(
                    patient.patient_id, "auditing", processing_time_ms
                )
                
                if grievance.status == "Not Consistent":
                    self.logger.log_grievance_found(
                        patient.patient_id,
                        grievance.total_inconsistencies,
                        grievance.correction_needed
                    )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to audit patient record",
                    patient_id=patient.patient_id,
                    error=str(e)
                )
        
        inconsistent_count = len([g for g in grievances if g.status == "Not Consistent"])
        self.logger.info(
            f"Audit step completed",
            total_records=len(patient_records),
            inconsistent_records=inconsistent_count,
            consistency_rate=(len(patient_records) - inconsistent_count) / len(patient_records)
        )
        
        return grievances
    
    def _run_verification_step(self, grievances: List[GrievanceReport]) -> Dict[str, Any]:
        """Run verification step for inconsistent records."""
        self.logger.info("Starting verification step")
        
        inconsistent_grievances = [g for g in grievances if g.status == "Not Consistent"]
        
        if not inconsistent_grievances:
            self.logger.info("No inconsistent records found, skipping verification")
            return {}
        
        results = {}
        
        # WhatsApp verification for user data issues
        if self.whatsapp_verifier:
            whatsapp_results = self.whatsapp_verifier.send_verification_messages(inconsistent_grievances)
            results["whatsapp"] = whatsapp_results
        
        # Doctor verification for clinical issues
        if self.doctor_verifier:
            doctor_results = self.doctor_verifier.send_verification_requests(inconsistent_grievances)
            results["doctor"] = doctor_results
        
        self.logger.info(
            f"Verification step completed",
            inconsistent_records=len(inconsistent_grievances),
            whatsapp_sent=len(results.get("whatsapp", [])),
            doctor_requests_sent=len(results.get("doctor", []))
        )
        
        return results
    
    def _run_resolution_step(self, patient_records: List[PatientRecord], grievances: List[GrievanceReport]) -> List[PatientRecord]:
        """Run resolution step to correct identified issues."""
        self.logger.info("Starting resolution step")
        
        corrected_records = []
        
        # Create mapping of patient_id to grievance
        grievance_map = {g.patient_id: g for g in grievances}
        
        for patient in patient_records:
            grievance = grievance_map.get(patient.patient_id)
            
            try:
                corrected_patient = self.resolver.resolve_patient_record(patient, grievance)
                corrected_records.append(corrected_patient)
                
                if grievance and grievance.status == "Not Consistent":
                    self.logger.info(
                        f"Patient record resolved",
                        patient_id=patient.patient_id,
                        issues_resolved=grievance.total_inconsistencies
                    )
                
            except Exception as e:
                self.logger.error(
                    f"Failed to resolve patient record",
                    patient_id=patient.patient_id,
                    error=str(e)
                )
                corrected_records.append(patient)  # Use original if resolution fails
        
        self.logger.info(
            f"Resolution step completed",
            total_records=len(patient_records),
            corrected_records=len(corrected_records)
        )
        
        return corrected_records
    
    def _save_results(self, corrected_records: List[PatientRecord], grievances: List[GrievanceReport]) -> Dict[str, str]:
        """Save pipeline results."""
        output_dir = Path(self.config.storage.output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save corrected patient data
        corrected_json_path = output_dir / "ehr_corrected.json"
        corrected_csv_path = output_dir / "ehr_corrected.csv"
        
        # JSON format
        import json
        with open(corrected_json_path, 'w', encoding='utf-8') as f:
            json.dump([patient.to_dict() for patient in corrected_records], f, indent=2, ensure_ascii=False)
        
        # CSV format
        import pandas as pd
        df = pd.DataFrame([patient.to_dict() for patient in corrected_records])
        df.to_csv(corrected_csv_path, index=False)
        
        # Create storage summary
        summary = self.storage.create_summary_report()
        
        self.logger.info(
            f"Results saved",
            json_output=str(corrected_json_path),
            csv_output=str(corrected_csv_path),
            summary_report=str(output_dir / "storage_summary.json")
        )
        
        return {
            "corrected_json": str(corrected_json_path),
            "corrected_csv": str(corrected_csv_path),
            "storage_summary": str(output_dir / "storage_summary.json")
        }
    
    def _generate_summary(self, patient_records: List[PatientRecord], grievances: List[GrievanceReport], 
                         verification_results: Dict[str, Any], processing_time_ms: int) -> Dict[str, Any]:
        """Generate pipeline execution summary."""
        total_patients = len(patient_records)
        inconsistent_patients = len([g for g in grievances if g.status == "Not Consistent"])
        total_inconsistencies = sum(g.total_inconsistencies for g in grievances)
        
        summary = {
            "execution_time": {
                "total_processing_time_ms": processing_time_ms,
                "average_time_per_patient_ms": processing_time_ms / total_patients if total_patients > 0 else 0
            },
            "patient_statistics": {
                "total_patients": total_patients,
                "consistent_patients": total_patients - inconsistent_patients,
                "inconsistent_patients": inconsistent_patients,
                "consistency_rate": (total_patients - inconsistent_patients) / total_patients if total_patients > 0 else 0
            },
            "grievance_statistics": {
                "total_inconsistencies": total_inconsistencies,
                "average_inconsistencies_per_patient": total_inconsistencies / total_patients if total_patients > 0 else 0
            },
            "verification_statistics": {
                "whatsapp_messages_sent": len(verification_results.get("whatsapp", [])),
                "doctor_requests_sent": len(verification_results.get("doctor", []))
            },
            "configuration": {
                "pipeline_version": self.config.app.version,
                "llm_provider": self.config.llm.provider,
                "storage_format": self.config.storage.default_format
            }
        }
        
        return summary
    
    def _should_run_verification(self) -> bool:
        """Check if verification step should be run."""
        return (self.config.verification.whatsapp_enabled or 
                self.config.verification.doctor_enabled)
    
    def _run_audit_only(self, input_data_path: str, demo_mode: bool = False, demo_count: int = 5) -> Dict[str, Any]:
        """Run only audit step."""
        patient_records = self._load_patient_data(input_data_path, demo_mode, demo_count)
        grievances = self._run_audit_step(patient_records)
        
        return {
            "grievances": grievances,
            "total_records": len(patient_records),
            "inconsistent_records": len([g for g in grievances if g.status == "Not Consistent"])
        }
    
    def _run_verification_only(self, **kwargs) -> Dict[str, Any]:
        """Run only verification step."""
        # Load existing grievances from storage
        grievances = self.storage.get_all_grievances()
        return self._run_verification_step(grievances)
    
    def _run_resolution_only(self, input_data_path: str, demo_mode: bool = False, demo_count: int = 5) -> Dict[str, Any]:
        """Run only resolution step."""
        patient_records = self._load_patient_data(input_data_path, demo_mode, demo_count)
        
        # Load existing grievances
        grievances = self.storage.get_all_grievances()
        grievance_map = {g.patient_id: g for g in grievances}
        
        corrected_records = []
        for patient in patient_records:
            grievance = grievance_map.get(patient.patient_id)
            corrected_patient = self.resolver.resolve_patient_record(patient, grievance)
            corrected_records.append(corrected_patient)
        
        # Save results
        output_paths = self._save_results(corrected_records, grievances)
        
        return {
            "corrected_records": len(corrected_records),
            "output_paths": output_paths
        }
