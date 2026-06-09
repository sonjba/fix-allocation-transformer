"""Write flattened rows to a CSV file."""

import csv
from typing import List, Dict
from fix_alloc.target_schema import TARGET_COLUMNS


def write_csv(rows: List[Dict[str, str]], output_path: str) -> None:
    """
    Write row dicts to a CSV file using the target schema column order.

    Args:
        rows: list of {column_name: value} dicts (from flatten())
        output_path: path to the output .csv file
    """
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TARGET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)