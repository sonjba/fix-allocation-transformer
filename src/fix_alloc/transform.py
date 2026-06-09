"""Flatten a domain AllocationInstruction into CSV rows."""

from typing import List, Dict
from fix_alloc.model import AllocationInstruction
from fix_alloc.parties import resolve_parties


def flatten(instruction: AllocationInstruction) -> List[Dict[str, str]]:
    """
    Flatten one AllocationInstruction into a list of row dicts.

    One row per allocation. Trade-level fields and resolved party columns
    repeat on every row; allocation-level fields vary per row.

    Returns:
        A list of {column_name: value} dicts, one per allocation.
    """
    # Trade-level fields — identical on every row
    trade_fields = {
        "alloc_id": instruction.alloc_id,
        "alloc_trans_type": instruction.alloc_trans_type,
        "side": instruction.side,
        "symbol": instruction.symbol,
        "trade_quantity": instruction.quantity,
    }

    # Resolved party columns — also identical on every row
    party_fields = resolve_parties(instruction.parties)

    # One row per allocation
    rows = []
    for alloc in instruction.allocations:
        alloc_fields = {
            "individual_alloc_id": alloc.individual_alloc_id,
            "alloc_account": alloc.account,
            "alloc_qty": alloc.quantity,
            "alloc_price": alloc.price,
        }
        row = {**trade_fields, **alloc_fields, **party_fields}
        rows.append(row)

    return rows

def deduplicate(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate rows so processing is idempotent.

    Re-sent or re-processed messages (a FIX resend, or a batch file run
    twice) shouldn't produce duplicate output. We keep the first occurrence
    of each allocation and drop later duplicates.

    Dedup key: (alloc_id, individual_alloc_id, alloc_account).
    IndividualAllocID alone would be ideal, but it's optional in FIX and may
    be blank — so we include alloc_account so distinct allocations within one
    message don't collide.

    Returns:
        A new list with duplicates removed, original order preserved.
    """
    seen = set()
    unique_rows = []
    for row in rows:
        key = (row["alloc_id"], row["individual_alloc_id"], row["alloc_account"])
        if key not in seen:
            seen.add(key)
            unique_rows.append(row)
    return unique_rows