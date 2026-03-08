"""
Load EHR data from CSV and save as JSON for the auditor.
"""

import json
from pathlib import Path
from typing import Union

import pandas as pd


def load_csv_to_json(
    csv_path: Union[str, Path] = "ehr_messy.csv",
    json_path: Union[str, Path] = "ehr_messy.json",
) -> Path:
    """
    Read CSV and write records as JSON. Returns path to the JSON file.
    """
    csv_path = Path(csv_path)
    json_path = Path(json_path)
    df = pd.read_csv(csv_path)
    records = df.to_dict(orient="records")
    with open(json_path, "w") as f:
        json.dump(records, f, indent=2)
    return json_path


if __name__ == "__main__":
    base = Path(__file__).parent
    load_csv_to_json(base / "ehr_messy.csv", base / "ehr_messy.json")