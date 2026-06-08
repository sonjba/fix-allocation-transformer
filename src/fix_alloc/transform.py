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