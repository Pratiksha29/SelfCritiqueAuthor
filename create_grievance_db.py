#!/usr/bin/env python3
"""
Store grievance reports in SQLite database for full text preservation.
"""

import sqlite3
import json
import pandas as pd
from pathlib import Path

def create_grievance_db(csv_path: str, db_path: str = "grievance_reports.db"):
    """Create SQLite database with full grievance reports."""
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grievance_reports (
            patient_id TEXT PRIMARY KEY,
            name TEXT,
            age INTEGER,
            gender TEXT,
            medical_condition TEXT,
            consistent_or_not TEXT,
            grievance_report TEXT,
            full_patient_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert records
    for _, row in df.iterrows():
        cursor.execute('''
            INSERT OR REPLACE INTO grievance_reports 
            (patient_id, name, age, gender, medical_condition, consistent_or_not, 
             grievance_report, full_patient_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row['Patient_ID'],
            row['Name'],
            row['Age'],
            row['Gender'],
            row['Medical Condition'],
            row['Consistent_or_Not'],
            row['Grievance_Report'],
            json.dumps(row.to_dict())
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database created: {db_path}")
    print(f"📊 Stored {len(df)} grievance reports")
    
    return db_path

def query_grievance(db_path: str, patient_id: str = None):
    """Query grievance reports from database."""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if patient_id:
        cursor.execute('SELECT * FROM grievance_reports WHERE patient_id = ?', (patient_id,))
        results = cursor.fetchone()
    else:
        cursor.execute('SELECT patient_id, name, consistent_or_not, grievance_report FROM grievance_reports')
        results = cursor.fetchall()
    
    conn.close()
    return results

if __name__ == "__main__":
    # Create database
    db_path = create_grievance_db("audit_report.csv")
    
    # Example query
    print("\n📋 Sample query results:")
    results = query_grievance(db_path)
    for result in results[:3]:  # Show first 3
        print(f"Patient {result[0]} ({result[1]}): {result[2]}")
