"""
Add cell_number column to EHR data.
"""

import pandas as pd
from pathlib import Path
import random


def generate_phone_numbers():
    """Generate realistic US phone numbers."""
    area_codes = [
        '212', '646', '917', '718', '347',  # NYC
        '310', '424', '323', '213', '818',  # LA
        '312', '773', '872', '630', '708',  # Chicago
        '415', '510', '650', '408', '925',  # SF Bay Area
    ]
    
    phones = []
    for _ in range(2000):  # Generate for all records
        area = random.choice(area_codes)
        exchange = f"{random.randint(200, 999):03d}"
        number = f"{random.randint(1000, 9999):04d}"
        phones.append(f"+1-{area}-{exchange}-{number}")
    
    return phones


def add_cell_numbers():
    """Add cell_number column to the existing CSV."""
    csv_path = Path(__file__).parent / "ehr_messy.csv"
    backup_path = Path(__file__).parent / "ehr_messy_backup.csv"
    
    # Read existing data
    df = pd.read_csv(csv_path)
    
    # Create backup
    df.to_csv(backup_path, index=False)
    print(f"✅ Created backup: {backup_path}")
    
    # Generate phone numbers
    phone_numbers = generate_phone_numbers()
    
    # Add cell_number column
    df['cell_number'] = phone_numbers[:len(df)]
    
    # Reorder columns to put cell_number after Patient_ID
    cols = list(df.columns)
    patient_id_idx = cols.index('Patient_ID')
    cols.insert(patient_id_idx + 1, 'cell_number')
    cols.remove('cell_number')
    df = df[cols]
    
    # Save updated data
    df.to_csv(csv_path, index=False)
    print(f"✅ Updated {csv_path} with cell_number column")
    print(f"📊 Added {len(df)} phone numbers")
    
    # Show sample
    print("\n📋 Sample data with phone numbers:")
    print(df[['Patient_ID', 'cell_number', 'Name']].head())


if __name__ == "__main__":
    add_cell_numbers()
