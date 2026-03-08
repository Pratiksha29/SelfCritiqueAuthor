"""
Corrupt a clean EHR dataset for testing data-cleaning agent capabilities.
Randomly selects 30% of records and applies real-world inconsistencies.
The other 70% remains clean for before/after comparison.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ---------------------------------------------------------------------------
# Configuration: load your EHR data (adjust path/columns if needed)
# ---------------------------------------------------------------------------
CSV_PATH = "smaller_set.csv"
OUTPUT_PATH = "ehr_messy.csv"  # optional: save df_messy
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# Column name mapping (your CSV uses these; we add Patient_ID, Date_of_Birth, Weight, Height)
COL_NAME = "Name"
COL_GENDER = "Gender"
COL_ADMISSION = "Date of Admission"
COL_DISCHARGE = "Discharge Date"
COL_DIAGNOSIS = "Medical Condition"
COL_AGE = "Age"


def load_and_augment(df: pd.DataFrame) -> pd.DataFrame:
    """Add synthetic Patient_ID, Date_of_Birth, Weight, Height for corruption tasks."""
    df = df.copy()
    n = len(df)

    # Patient_ID (stable for identity resolution)
    df["Patient_ID"] = [f"PID-{i:06d}" for i in range(n)]

    # Date_of_Birth: approximate from Age and admission date (year only for simplicity)
    def approx_dob(row):
        try:
            adm = pd.to_datetime(row[COL_ADMISSION], errors="coerce")
            if pd.isna(adm):
                return "01/15/1990"
            year = adm.year - int(row[COL_AGE])
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            return f"{month:02d}/{day:02d}/{year}"
        except Exception:
            return "01/15/1990"

    df["Date_of_Birth"] = df.apply(approx_dob, axis=1)

    # Synthetic Weight (kg) and Height (cm) - realistic ranges
    df["Weight"] = np.round(np.random.uniform(50, 120, n), 1)
    df["Height"] = np.round(np.random.uniform(150, 200, n), 1)

    return df


def near_duplicate_name(name: str) -> str:
    """Create a plausible near-duplicate of a name (typos, abbreviation)."""
    variants = []
    parts = name.strip().split()
    if len(parts) >= 2:
        first, last = parts[0], parts[-1]
        # Abbreviation: "John Smith" -> "J. Smith"
        variants.append(f"{first[0]}. {last}")
        # Typo in first name: double letter or wrong vowel
        if len(first) > 2:
            typo_first = first[0] + first[2] + first[1] + first[3:] if len(first) > 3 else first[:2] + first[0]
            variants.append(f"{typo_first} {last}")
        # Nickname / spelling: "Jon" for "John", "Kathy" for "Katherine"
        if first.lower() == "john":
            variants.append(f"Jon {last}")
        elif first.lower() == "catherine" or first.lower() == "katherine":
            variants.append(f"Kathy {last}")
        elif first.lower() == "robert":
            variants.append(f"Rob {last}")
        elif first.lower() == "william":
            variants.append(f"Bill {last}")
        elif first.lower() == "michael":
            variants.append(f"Mike {last}")
    if not variants:
        return name
    return random.choice(variants)


def corrupt_identity_resolution(df: pd.DataFrame, indices: np.ndarray, n: int = 100) -> None:
    """In 100 records, make Name a near-duplicate; Patient_ID and Date_of_Birth unchanged."""
    to_corrupt = random.sample(list(indices), min(n, len(indices)))
    for i in to_corrupt:
        df.loc[i, COL_NAME] = near_duplicate_name(str(df.loc[i, COL_NAME]))


def corrupt_unit_ambiguity(df: pd.DataFrame, indices: np.ndarray) -> None:
    """Randomly express Weight/Height in Imperial (lbs/in) or Metric (kg/cm) without labels."""
    for i in indices:
        if random.random() < 0.5:
            # Store as Imperial: Weight in lbs, Height in inches
            kg = df.loc[i, "Weight"]
            cm = df.loc[i, "Height"]
            df.loc[i, "Weight"] = round(kg * 2.205, 1)
            df.loc[i, "Height"] = round(cm / 2.54, 1)
        # else leave in metric (kg, cm) - no label added


def corrupt_temporal_paradox(df: pd.DataFrame, indices: np.ndarray, n: int = 50) -> None:
    """Swap Admission and Discharge dates in 50 records."""
    to_swap = random.sample(list(indices), min(n, len(indices)))
    for i in to_swap:
        adm = df.loc[i, COL_ADMISSION]
        dis = df.loc[i, COL_DISCHARGE]
        df.loc[i, COL_ADMISSION] = dis
        df.loc[i, COL_DISCHARGE] = adm


# Diagnosis -> synonym/abbreviation mapping (semantic noise)
DIAGNOSIS_SYNONYMS = {
    "Hypertension": ["HTN", "High BP", "Elevated BP", "HBP"],
    "Diabetes": ["T2DM", "DM2", "Type 2 DM", "Diabetes Mellitus"],
    "Asthma": ["Reactive airway", "Bronchial asthma", "ASTHMA"],
    "Cancer": ["CA", "Malignancy", "Neoplasm"],
    "Obesity": ["OB", "BMI elevated", "Morbid obesity"],
    "Arthritis": ["DJD", "Degenerative joint", "ARTH"],
}


def corrupt_semantic_noise(df: pd.DataFrame, indices: np.ndarray) -> None:
    """Replace standard terms in Diagnosis with synonyms/abbreviations."""
    for i in indices:
        cond = df.loc[i, COL_DIAGNOSIS]
        if cond in DIAGNOSIS_SYNONYMS:
            df.loc[i, COL_DIAGNOSIS] = random.choice(DIAGNOSIS_SYNONYMS[cond])


# Conditions typically associated with one gender (for categorical mismatch)
FEMALE_TYPICAL = ["Pregnancy", "Ovarian Cancer", "Breast Cancer"]
MALE_TYPICAL = ["Prostate Cancer", "Erectile dysfunction"]


def corrupt_categorical_mismatch(df: pd.DataFrame, indices: np.ndarray, n: int = 30) -> None:
    """Create 30 fat-finger errors: Gender does not align with diagnosis."""
    pool = list(indices)
    random.shuffle(pool)
    count = 0
    for i in pool:
        if count >= n:
            break
        current_gender = str(df.loc[i, COL_GENDER]).strip().lower()
        if current_gender == "male":
            df.loc[i, COL_DIAGNOSIS] = random.choice(FEMALE_TYPICAL)
            count += 1
        elif current_gender == "female":
            df.loc[i, COL_DIAGNOSIS] = random.choice(MALE_TYPICAL)
            count += 1


def corrupt_format_shredding(df: pd.DataFrame, indices: np.ndarray) -> None:
    """Randomly change Date_of_Birth format to MM/DD/YYYY, DD-MM-YYYY, or YYYY.MM.DD."""
    for i in indices:
        dob = str(df.loc[i, "Date_of_Birth"])
        try:
            # Try to parse current format
            for fmt in ["%m/%d/%Y", "%d-%m-%Y", "%Y.%m.%d", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(dob, fmt)
                    break
                except ValueError:
                    continue
            else:
                # Fallback: assume MM/DD/YYYY
                parts = dob.replace("-", "/").replace(".", "/").split("/")
                if len(parts) == 3:
                    m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
                    if m > 12:
                        m, d = d, m
                    dt = datetime(y, m, d)
                else:
                    continue
        except Exception:
            continue

        choice = random.choice(["MM/DD/YYYY", "DD-MM-YYYY", "YYYY.MM.DD"])
        if choice == "MM/DD/YYYY":
            df.loc[i, "Date_of_Birth"] = dt.strftime("%m/%d/%Y")
        elif choice == "DD-MM-YYYY":
            df.loc[i, "Date_of_Birth"] = dt.strftime("%d-%m-%Y")
        else:
            df.loc[i, "Date_of_Birth"] = dt.strftime("%Y.%m.%d")


def main():
    df = pd.read_csv(CSV_PATH)
    n_total = len(df)
    assert n_total == 2000, f"Expected 2000 records, got {n_total}"

    # Add columns needed for corruptions
    df = load_and_augment(df)

    # 30% subset (600 records) to corrupt
    n_corrupt = int(round(0.30 * n_total))
    corrupt_idx = np.random.choice(df.index, size=n_corrupt, replace=False)

    # Apply corruptions (overlaps allowed except where counts are fixed)
    corrupt_identity_resolution(df, corrupt_idx, n=100)
    corrupt_unit_ambiguity(df, corrupt_idx)
    corrupt_temporal_paradox(df, corrupt_idx, n=50)
    corrupt_semantic_noise(df, corrupt_idx)
    corrupt_categorical_mismatch(df, corrupt_idx, n=30)
    corrupt_format_shredding(df, corrupt_idx)

    df_messy = df

    # Summary
    print("=" * 60)
    print("EHR CORRUPTION SUMMARY")
    print("=" * 60)
    print(f"Total records:                    {n_total}")
    print(f"Records left clean (70%):         {n_total - n_corrupt}")
    print(f"Records in corrupted subset (30%): {n_corrupt}")
    print()
    print("Inconsistencies introduced in the 30% subset:")
    print("  • Identity resolution (near-duplicate names):  100 records")
    print("  • Unit ambiguity (Weight/Height imperial/metric): 600 records (mixed)")
    print("  • Temporal paradoxes (admission/discharge swap):  50 records")
    print("  • Semantic noise (diagnosis synonyms/abbrev):    up to 600 (where mapped)")
    print("  • Categorical mismatch (gender vs diagnosis):     30 records")
    print("  • Format shredding (Date_of_Birth formats):      600 records")
    print("=" * 60)
    print(f"Messy dataframe assigned to: df_messy (shape {df_messy.shape})")
    print("=" * 60)

    df_messy.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved to: {OUTPUT_PATH}")

    return df_messy


if __name__ == "__main__":
    df_messy = main()
