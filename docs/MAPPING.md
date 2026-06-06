# FIX AllocationInstruction (J) Mapping Specification

## Overview

This document specifies how FIX 4.4 AllocationInstruction (MsgType `J`) messages are transformed into a flat CSV output, with one row per account allocation.

## FIX 4.4 AllocationInstruction Fields

The following fields from the FIX 4.4 specification are handled:

| Level | Field | Tag | Purpose |
|---|---|---|---|
| Header | BeginString | 8 | Protocol version |
| Header | BodyLength | 9 | Message body size |
| Header | MsgType | 35 | Message type (J) |
| Header | SenderCompID | 49 | Sending firm |
| Header | TargetCompID | 56 | Target firm |
| Header | MsgSeqNum | 34 | Sequence number |
| Header | SendingTime | 52 | Timestamp |
| Trade | AllocID | 70 | Allocation identifier |
| Trade | AllocTransType | 71 | New / Replace / Cancel |
| Trade | RefAllocID | 72 | Reference alloc ID (for replace/cancel) |
| Trade | Side | 54 | Buy/Sell |
| Trade | Symbol | 55 | Security identifier |
| Trade | Quantity | 53 | Total quantity |
| Orders | NoOrders | 73 | Count of orders |
| Orders | OrderID | 37 | Individual order ID |
| Allocations | NoAllocs | 78 | Count of account allocations |
| Allocations | AllocAccount | 79 | Account to allocate to |
| Allocations | AllocQty | 80 | Quantity for this account |
| Allocations | AllocPrice | 366 | Price for this allocation |
| Allocations | IndividualAllocID | 467 | Unique ID for this allocation |
| Parties | NoPartyIDs | 453 | Count of parties |
| Parties | PartyID | 448 | Party identifier |
| Parties | PartyIDSource | 447 | Type of identifier (BIC, D-U-N-S, etc.) |
| Parties | PartyRole | 452 | Role of party (see PartyRole mapping below) |
| Trailer | CheckSum | 10 | Message checksum |

## PartyRole Mapping

Party roles identified by tag 452:

| PartyRole Code | Description | Target Column |
|---|---|---|
| 1 | Executing Firm | executing_firm |
| 3 | Client ID | client_id |
| 4 | Clearing Firm | clearing_firm |
| 5 | Investor ID | investor_id |
| 6 | Introducing Firm | introducing_firm |
| 13 | Order Origination Firm | order_origin_firm |
| 14 | Giveup Clearing Firm | giveup_clearing_firm |


## Target CSV Schema

Output is one row per account allocation. The columns are:

| Column | Source | Cardinality | Notes |
|---|---|---|---|
| alloc_id | AllocID (70) | Trade-level (repeats) | Same for all rows from one message |
| alloc_trans_type | AllocTransType (71) | Trade-level (repeats) | New, Replace, or Cancel |
| side | Side (54) | Trade-level (repeats) | Buy or Sell |
| symbol | Symbol (55) | Trade-level (repeats) | Security identifier |
| trade_quantity | Quantity (53) | Trade-level (repeats) | Total quantity traded |
| individual_alloc_id | IndividualAllocID (467) | Allocation-level (varies) | Unique per account allocation |
| alloc_account | AllocAccount (79) | Allocation-level (varies) | Account receiving this allocation |
| alloc_qty | AllocQty (80) | Allocation-level (varies) | Quantity for this account |
| alloc_price | AllocPrice (366) | Allocation-level (varies) | Price for this account (if specified) |
| executing_firm | PartyRole 1 | Party-level (resolved) | Executing Firm (from Parties group) |
| clearing_firm | PartyRole 4 | Party-level (resolved) | Clearing Firm (from Parties group) |
| client_id | PartyRole 3 | Party-level (resolved) | Client ID (from Parties group) |
| investor_id | PartyRole 5 | Party-level (resolved) | Investor ID (from Parties group) |
| giveup_clearing_firm | PartyRole 14 | Party-level (resolved) | Giveup Clearing Firm (from Parties group) |


## Flattening Rule

**One row per account allocation.** Trade-level fields (AllocID, Side, Symbol, Quantity, AllocTransType, etc.) are repeated across all rows generated from a single FIX message. For each entry in the NoAllocs repeating group, one output row is created, containing: the repeated trade-level data, the allocation-level data (AllocAccount, AllocQty, AllocPrice, IndividualAllocID), and resolved parties from the Parties group. If a party role is not present in the message, the corresponding column is left blank.