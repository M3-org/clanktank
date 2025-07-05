#!/usr/bin/env python3
"""
Test script to process CSV data directly and populate the database.
This simulates the Google Sheets workflow using the existing blocktank.csv file.
"""

import csv
import sys
import os

from sheet_processor import create_database, insert_or_update_pitch

def process_csv_to_db(csv_file, db_file):
    """Process CSV file and populate database."""
    
    # Create database
    create_database(db_file)
    
    # Read CSV file
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Get headers
        
        processed = 0
        for row in reader:
            try:
                insert_or_update_pitch(db_file, row, headers)
                processed += 1
                print(f"Processed submission: {row[0]}")  # submission_id is first column
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
    
    print(f"Successfully processed {processed} submissions")

if __name__ == "__main__":
    csv_file = "../blocktank.csv"  # CSV is in parent directory
    db_file = "../test_pitches.db"  # Output to parent directory
    
    if not os.path.exists(csv_file):
        print(f"CSV file {csv_file} not found")
        sys.exit(1)
    
    process_csv_to_db(csv_file, db_file)
    print(f"Database created: {db_file}")