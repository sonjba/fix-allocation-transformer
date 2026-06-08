"""Ordered list of output CSV columns."""

# Trade-level columns (repeat across all rows from one message)
TRADE_COLUMNS = [
    "alloc_id",
    "alloc_trans_type",
    "side",
    "symbol",
    "trade_quantity",
]

# Allocation-level columns (unique values per row)
ALLOCATION_COLUMNS = [
    "individual_alloc_id",
    "alloc_account",
    "alloc_qty",
    "alloc_price",
]

# Resolved party columns (repeat across all rows from one message)
PARTY_COLUMNS = [
    "executing_firm",
    "clearing_firm",
    "client_id",
    "investor_id",
    "introducing_firm",
    "order_origin_firm",
    "giveup_clearing_firm",
]

# The full ordered output schema
TARGET_COLUMNS = TRADE_COLUMNS + ALLOCATION_COLUMNS + PARTY_COLUMNS