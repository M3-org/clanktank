#!/usr/bin/env python3
"""Test the updated markdown formatting."""

import csv
from sheet_processor import row_to_markdown

# Read one row from CSV to test markdown format
with open('../blocktank.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    headers = next(reader)
    first_row = next(reader)

# Generate markdown for the first submission
markdown_content, submission_id = row_to_markdown(first_row, headers)

print(f"Generated markdown for {submission_id}:")
print("=" * 50)
print(markdown_content)