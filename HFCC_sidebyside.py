import sqlite3
import pandas as pd
import sys
from itertools import zip_longest

def print_side_by_side_independent(a26_db_path, b26_db_path, a26_table, b26_table, output_path="side_by_side_output.txt"):
    # Redirect output to both terminal and text file
    class Tee(object):
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "w", encoding="utf-8")
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            self.terminal.flush()
            self.log.flush()

    sys.stdout = Tee(output_path)

    try:
        conn_a = sqlite3.connect(a26_db_path)
        conn_b = sqlite3.connect(b26_db_path)

        df_a = pd.read_sql(f"SELECT * FROM {a26_table}", conn_a)
        df_b = pd.read_sql(f"SELECT * FROM {b26_table}", conn_b)

        conn_a.close()
        conn_b.close()

        # Normalize column names to lowercase
        df_a.columns = [c.strip().lower() for c in df_a.columns]
        df_b.columns = [c.strip().lower() for c in df_b.columns]

        # Define sorting columns: broadcaster, language, start, stop, freq (handling 'freq' name variants if needed)
        freq_col_a = 'freq' if 'freq' in df_a.columns else 'frequency'
        freq_col_b = 'freq' if 'freq' in df_b.columns else 'frequency'

        sort_cols_a = [c for c in ['broadcaster', 'language', 'start', 'stop', freq_col_a] if c in df_a.columns]
        sort_cols_b = [c for c in ['broadcaster', 'language', 'start', 'stop', freq_col_b] if c in df_b.columns]

        # Sort each dataset independently
        df_a = df_a.sort_values(by=sort_cols_a, na_position='last')
        df_b = df_b.sort_values(by=sort_cols_b, na_position='last')

        print("=" * 130)
        print(f"INDEPENDENT SIDE-BY-SIDE DATASETS REPORT: {a26_table} vs {b26_table}")
        print("Grouped by Broadcaster -> Language | Sorted independently by Start, Stop, Frequency")
        print("=" * 130 + "\n")

        # Gather all unique broadcaster-language pairs from both datasets
        groups_a = set(df_a[['broadcaster', 'language']].dropna().itertuples(index=False, name=None)) if {'broadcaster', 'language'}.issubset(df_a.columns) else set()
        groups_b = set(df_b[['broadcaster', 'language']].dropna().itertuples(index=False, name=None)) if {'broadcaster', 'language'}.issubset(df_b.columns) else set()
        all_groups = sorted(list(groups_a.union(groups_b)))

        if not all_groups:
            all_groups = [(None, None)]

        # Specific fields to display
        target_fields = ['start', 'stop', 'freq', 'frequency', 'days', 'tx_code', 'pwr', 'azi', 'mod']

        for broadcaster, language in all_groups:
            bc_str = str(broadcaster) if not pd.isna(broadcaster) else "UNKNOWN"
            lang_str = str(language) if not pd.isna(language) else "UNKNOWN"

            # Filter independent subsets for this group
            subset_a = df_a[(df_a['broadcaster'] == broadcaster) & (df_a['language'] == language)] if broadcaster is not None else df_a
            subset_b = df_b[(df_b['broadcaster'] == broadcaster) & (df_b['language'] == language)] if broadcaster is not None else df_b

            print(f"Broadcaster: {bc_str}  |  Language: {lang_str}")
            print("-" * 130)
            
            # Display captions above the tables side-by-side
            caption_a = f"[{a26_table}]"
            caption_b = f"[{b26_table}]"
            print(f"{caption_a.ljust(60)}  |  {caption_b}")
            print("-" * 130)

            # Format rows containing only the specified variables
            rows_a = []
            for _, r in subset_a.iterrows():
                parts = []
                for f in target_fields:
                    if f in r and not pd.isna(r[f]):
                        val_str = str(r[f])
                        # Apply specific formatting rules
                        if f in ['freq', 'frequency']:
                            val_str = val_str.rjust(5)  # 5 characters wide, leading spaces
                        elif f == 'days':
                            val_str = val_str.rjust(7)
                        elif f == 'tx_code':
                            val_str = val_str.ljust(3)  # 3 characters wide, trailing spaces
                        elif f == 'pwr':
                            val_str = val_str.rjust(3)
                        parts.append(val_str)
                rows_a.append("   ".join(parts))

            rows_b = []
            for _, r in subset_b.iterrows():
                parts = []
                for f in target_fields:
                    if f in r and not pd.isna(r[f]):
                        val_str = str(r[f])
                        if f in ['freq', 'frequency']:
                            val_str = val_str.rjust(5)
                        elif f == 'days':
                            val_str = val_str.rjust(7)
                        elif f == 'tx_code':
                            val_str = val_str.ljust(3)
                        elif f == 'pwr':
                            val_str = val_str.ljust(3)
                        parts.append(val_str)
                rows_b.append("   ".join(parts))

            # Determine padding width based on A entries so columns align nicely
            max_len_a = max([len(s) for s in rows_a]) if rows_a else 60
            padding_width = max(max_len_a, 60)

            # Print side-by-side line by line using zip_longest
            for entry_a, entry_b in zip_longest(rows_a, rows_b, fillvalue=""):
                padded_a = entry_a.ljust(padding_width)
                print(f"{padded_a}  |  {entry_b}")

            print("=" * 130 + "\n")

        print(f"[INFO] Side-by-side independent report successfully written to {output_path}")

    except Exception as e:
        print(f"[ERROR] An error occurred during report generation: {e}")

if __name__ == "__main__":
    # --- CONFIGURABLE VARIABLES ---
    A26_DB_PATH = "a26.db"
    B26_DB_PATH = "b26.db"
    A26_TABLE = "A26"
    B26_TABLE = "B26"
    OUTPUT_PATH = "side_by_side_output.txt"
    # ----------------------------

    print_side_by_side_independent(
        a26_db_path=A26_DB_PATH,
        b26_db_path=B26_DB_PATH,
        a26_table=A26_TABLE,
        b26_table=B26_TABLE,
        output_path=OUTPUT_PATH
    )