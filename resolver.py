"""
Resolver: Correct inconsistent EHR data based on grievance reports from the auditor.
Reads audit_report.csv and applies rule-based fixes for known inconsistency types.
Outputs corrected dataset (CSV and optional JSON) without audit columns.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

import pandas as pd

# Paths (override via function args)
DEFAULT_AUDIT_CSV = Path(__file__).parent / "audit_report.csv"
DEFAULT_OUTPUT_CSV = Path(__file__).parent / "ehr_corrected.csv"
DEFAULT_OUTPUT_JSON = Path(__file__).parent / "ehr_corrected.json"

# Diagnosis: abbreviation/slang -> canonical (per auditor standards)
DIAGNOSIS_NORMALIZE = {
    "HTN": "Hypertension",
    "HBP": "Hypertension",
    "HIGH BP": "Hypertension",
    "ELEVATED BP": "Hypertension",
    "T2DM": "Type 2 Diabetes Mellitus",
    "DM2": "Type 2 Diabetes Mellitus",
    "TYPE 2 DM": "Type 2 Diabetes Mellitus",
    "DIABETES MELLITUS": "Diabetes",
    "CA": "Cancer",
    "MALIGNANCY": "Cancer",
    "NEOPLASM": "Cancer",
    "OB": "Obesity",
    "BMI ELEVATED": "Obesity",
    "MORBID OBESITY": "Obesity",
    "DJD": "Arthritis",
    "DEGENERATIVE JOINT": "Arthritis",
    "ARTH": "Arthritis",
    "REACTIVE AIRWAY": "Asthma",
    "BRONCHIAL ASTHMA": "Asthma",
}
# Female-typical diagnoses that were wrongly assigned to Male (revert to a neutral default)
FEMALE_TYPICAL_DIAGNOSES = {"Pregnancy", "Ovarian Cancer", "Breast Cancer"}
# Male-typical diagnoses wrongly assigned to Female
MALE_TYPICAL_DIAGNOSES = {"Prostate Cancer", "Erectile dysfunction"}


def _parse_date_loose(s: str) -> Optional[datetime]:
    """Try to parse date in MM/DD/YYYY, DD-MM-YYYY, YYYY.MM.DD, YYYY-MM-DD."""
    if not s or pd.isna(s):
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y", "%Y.%m.%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    # Try splitting and infer
    for sep in ("/", "-", "."):
        parts = s.split(sep)
        if len(parts) == 3:
            try:
                a, b, c = int(parts[0]), int(parts[1]), int(parts[2])
                if a > 31:  # year first
                    y, m, d = a, b, c
                elif c > 31:
                    m, d, y = a, b, c
                else:
                    m, d, y = a, b, c
                return datetime(y, m, d)
            except (ValueError, TypeError):
                pass
    return None


def _normalize_diagnosis(condition: str) -> str:
    """Return canonical diagnosis name if we have a mapping."""
    if not condition:
        return condition
    key = condition.strip()
    return DIAGNOSIS_NORMALIZE.get(key, condition)


def _apply_corrections(row: Dict[str, Any], grievance: str) -> Dict[str, Any]:
    """
    Apply rule-based corrections based on grievance text.
    Modifies a copy of the row and returns it.
    """
    out = dict(row)
    g = (grievance or "").upper()

    # Skip API/ERROR grievances - nothing to fix in data
    if "ERROR:" in (grievance or "") or "429" in (grievance or "") or "QUOTA" in g:
        return out

    # 1) Temporal: Discharge before Admission -> swap
    if "DISCHARGE" in g and "ADMISSION" in g and "BEFORE" in g:
        adm = out.get("Date of Admission")
        dis = out.get("Discharge Date")
        if adm and dis:
            adm_dt = _parse_date_loose(str(adm))
            dis_dt = _parse_date_loose(str(dis))
            if adm_dt and dis_dt and dis_dt < adm_dt:
                out["Date of Admission"] = dis
                out["Discharge Date"] = adm

    # 2) Diagnosis normalization (abbreviations -> canonical)
    cond = out.get("Medical Condition")
    if cond:
        normalized = _normalize_diagnosis(str(cond).strip())
        if normalized != cond:
            out["Medical Condition"] = normalized

    # 3) Gender-diagnosis mismatch: revert impossible diagnosis to a plausible one
    gender = (str(out.get("Gender", "")).strip()).lower()
    cond = str(out.get("Medical Condition", "")).strip()
    if gender == "male" and cond in FEMALE_TYPICAL_DIAGNOSES:
        out["Medical Condition"] = "Diabetes"  # neutral fallback
    if gender == "female" and cond in MALE_TYPICAL_DIAGNOSES:
        out["Medical Condition"] = "Hypertension"  # neutral fallback

    # 4) Date_of_Birth format: normalize to YYYY-MM-DD
    dob = out.get("Date_of_Birth")
    if dob:
        dt = _parse_date_loose(str(dob))
        if dt:
            out["Date_of_Birth"] = dt.strftime("%Y-%m-%d")

    return out


def resolve(
    audit_csv_path: Union[str, Path] = DEFAULT_AUDIT_CSV,
    output_csv_path: Union[str, Path] = DEFAULT_OUTPUT_CSV,
    output_json_path: Union[str, Path, None] = DEFAULT_OUTPUT_JSON,
) -> pd.DataFrame:
    """
    Read audit_report.csv, correct inconsistent rows based on Grievance_Report,
    and write corrected data (without audit columns) to CSV and optionally JSON.

    Returns the corrected DataFrame.
    """
    path = Path(audit_csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Audit CSV not found: {path}")

    df = pd.read_csv(path)
    if "Consistent_or_Not" not in df.columns or "Grievance_Report" not in df.columns:
        raise ValueError("audit_report.csv must contain columns: Consistent_or_Not, Grievance_Report")

    # Drop audit columns for output schema
    audit_cols = ["Consistent_or_Not", "Grievance_Report"]
    data_cols = [c for c in df.columns if c not in audit_cols]

    rows = []
    for _, r in df.iterrows():
        row = r.to_dict()
        status = str(row.get("Consistent_or_Not", "")).strip()
        grievance = str(row.get("Grievance_Report", "")).strip()
        if status == "Not Consistent" and grievance and grievance != "NA":
            corrected = _apply_corrections(row, grievance)
        else:
            corrected = row
        # Output row without audit columns
        out_row = {k: corrected[k] for k in data_cols if k in corrected}
        rows.append(out_row)

    result = pd.DataFrame(rows)
    result.to_csv(output_csv_path, index=False, encoding="utf-8")

    if output_json_path:
        records = result.to_dict(orient="records")
        with open(output_json_path, "w") as f:
            json.dump(records, f, indent=2)

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Correct EHR data from audit grievance reports.")
    parser.add_argument("--audit-csv", default=DEFAULT_AUDIT_CSV, help="Path to audit_report.csv")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Path to output corrected CSV")
    parser.add_argument("--output-json", default=None, help="Path to output corrected JSON (default: ehr_corrected.json)")
    args = parser.parse_args()
    json_path = args.output_json if args.output_json else DEFAULT_OUTPUT_JSON
    df = resolve(audit_csv_path=args.audit_csv, output_csv_path=args.output_csv, output_json_path=json_path)
    print(f"Corrected {len(df)} records -> {args.output_csv}, {json_path}")


if __name__ == "__main__":
    main()
