import sqlite3
import pandas as pd
from collections import Counter
import random
import os

"""
    Processor script for a HFCC database file. Go to a schedule page for a given season (e.g. https://new.hfcc.org/data/b26/), download ZIP file provided, unpact the file whose filename contains "all00.TXT", and point to it in the script.
    The script removes some unnecessary data, and saves the fine-grained database in SQLite db file. Optionally, it also exports it to CSV.
"""

def process_schedule_file(file_path, db_name="b26.db", table_name="B26", export_csv=True, csv_output="B26.csv"):
    # Define the fixed-width column specifications (name, length, type)
    columns_spec = [
        ("freq", 6, int),
        ("start", 5, str),
        ("stop", 5, str),
        ("ciraf_zones", 31, str),
        ("tx_code", 4, str),
        ("pwr", 5, int),
        ("azi", 8, str),
        ("slew", 4, int),          # can be negative
        ("ant", 4, int),
        ("days", 8, str),
        ("from_date", 7, str),     # stored as string DDMMYY
        ("to_date", 7, str),       # stored as string DDMMYY
        ("mod", 2, str),           # special rule applied during parsing
        ("alt_frq", 6, int),
        ("language", 11, str),
        ("country", 4, str),
        ("broadcaster", 4, str),
        ("fmo", 4, str),
        ("req_#", 6, int),
        ("misc_notes", 28, str)  # rest of the line
    ]
    
    # Fields to keep as requested
    fields_to_keep = [
        'freq', 'start', 'stop', 'ciraf_zones', 'tx_code', 'pwr', 'azi', 
        'days', 'from_date', 'to_date', 'mod', 'language', 'country', 
        'broadcaster', 'fmo'
    ]
    
    print(f"Reading file: {file_path}...")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Actual data starts at line 8 (0-indexed line index 7)
    data_lines = lines[7:]
    
    # Step 1: Pick 20 random rows from the entire dataset to find the most repeated from_date and to_date
    sample_size = min(20, len(data_lines))
    sampled_lines = random.sample(data_lines, sample_size) if sample_size > 0 else []
    
    sample_from_dates = []
    sample_to_dates = []
    
    for line in sampled_lines:
        if not line.strip():
            continue
        # Extract fields to find indices
        current_pos = 0
        row_sample = {}
        for col_name, length, _ in columns_spec:
            if length is not None:
                val = line[current_pos:current_pos + length].strip()
                current_pos += length
            else:
                val = line[current_pos:].strip()
            row_sample[col_name] = val
        
        if row_sample.get('from_date'):
            sample_from_dates.append(row_sample['from_date'])
        if row_sample.get('to_date'):
            sample_to_dates.append(row_sample['to_date'])

    most_common_from = Counter(sample_from_dates).most_common(1)[0][0] if sample_from_dates else ""
    most_common_to = Counter(sample_to_dates).most_common(1)[0][0] if sample_to_dates else ""

    print(f"Detected default 'from_date': {most_common_from}")
    print(f"Detected default 'to_date': {most_common_to}")

    records = []
    
    # Step 2: Process all data lines

    for line in data_lines:
        if not line.strip():
            continue

        current_pos = 0
        record = {}

        for col_name, length, col_type in columns_spec:
            if length is not None:
                val_str = line[current_pos:current_pos + length]
                current_pos += length
            else:
                val_str = line[current_pos:]

            val_str = val_str.strip()

            if col_name == "mod":
                if val_str == 'N':
                    record[col_name] = "DRM"
                else:
                    record[col_name] = ""
            elif col_type is int:
                if val_str == "" or val_str == "-":
                    record[col_name] = None
                else:
                    try:
                        record[col_name] = int(val_str)
                    except ValueError:
                        record[col_name] = None
            else:
                record[col_name] = val_str if val_str != "" else None

        # Apply blanking rule if values match the most repeated ones
        if record.get('from_date') == most_common_from:
            record['from_date'] = ""
        if record.get('to_date') == most_common_to:
            record['to_date'] = ""

        # Filter record to keep only required variables
        filtered_record = {k: record[k] for k in fields_to_keep if k in record}
        records.append(filtered_record)

    df = pd.DataFrame(records)

    # Write to SQLite Database using variables
    print(f"Connecting to SQLite database '{db_name}' and writing to table '{table_name}'...")
    conn = sqlite3.connect(db_name)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    conn.close()
    print("Database import complete.")

    if export_csv:
        print(f"Exporting data to semicolon-separated CSV: {csv_output}...")
        df.to_csv(csv_output, sep=';', index=False, encoding='utf-8')
        print("CSV export complete.")

    print(f"Successfully processed {len(df)} records.")
    return df

	
if __name__ == "__main__":
    # --- CONFIGURABLE VARIABLES ---
    INPUT_FILE = "B26all00.TXT"
    DB_NAME = "B26.db"
    TABLE_NAME = "B26"
    EXPORT_CSV = True
    CSV_OUTPUT = "B26.csv"
    # ----------------------------

    if os.path.exists(INPUT_FILE):
        process_schedule_file(INPUT_FILE, db_name=DB_NAME, table_name=TABLE_NAME, export_csv=EXPORT_CSV, csv_output=CSV_OUTPUT)
    else:
        print(f"File '{INPUT_FILE}' not found. Please provide the correct path.")