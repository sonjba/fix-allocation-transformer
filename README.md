# FIX Allocation Transformer

A Python tool that parses FIX 4.4 **AllocationInstruction** (MsgType `J`) messages and flattens them into a clean CSV — one row per account allocation — with party resolution by role and validation.

> **Status: in active development.** Core parsing and transformation work end to end (see Roadmap below). A command-line interface and packaged sample files are in progress.

## What it does

When a broker executes a block trade and splits it across multiple client accounts, that split is sent as a FIX AllocationInstruction. This tool turns that message into a flat CSV that downstream systems can consume:

- Parses the raw FIX wire format (tokenizing, header/trailer, repeating groups)
- Reconstructs the **allocations** and **parties** repeating groups
- Resolves parties by role — executing firm, clearing firm, client, give-up clearing firm, etc.
- Flattens to one row per allocation, repeating trade-level fields
- Validates repeating-group counts (rejects messages where the declared count doesn't match the actual entries)
- Optional idempotent de-duplication, so a re-processed message doesn't double up

Runs on **synthetic** FIX data only — no real or confidential data involved.

## Requirements

- Python 3.10+

## Install

```bash
git clone https://github.com/sonjba/fix-allocation-transformer.git
cd fix-allocation-transformer
pip install -e ".[dev]"
```

## Usage (library)

The transformation pipeline is available as a library:

```python
from fix_alloc.parser import parse_allocation_instruction
from fix_alloc.model import build_instruction
from fix_alloc.transform import flatten
from fix_alloc.csv_writer import write_csv

parsed = parse_allocation_instruction(fix_message)
instruction = build_instruction(parsed)
rows = flatten(instruction)
write_csv(rows, "allocations.csv")
```

A `fix-alloc` command-line interface is in progress (see Roadmap).

## Run the tests

```bash
pytest
```

## Mapping specification

The FIX-to-CSV field mapping, target schema, and party-role resolution rules are documented in [`docs/MAPPING.md`](docs/MAPPING.md).

## Scope

This is a **transformer**, not a full FIX session/engine. It handles the application-layer task of turning a received AllocationInstruction into a flat internal format. Session management and transport (logon, heartbeats, sequencing, message framing) are out of scope — in production, those are handled by a FIX engine upstream.

## Roadmap

- [x] Package scaffold and mapping specification
- [x] FIX wire parser with repeating-group reconstruction
- [x] Domain model and party resolution (incl. give-up scenario)
- [x] Transform to CSV with idempotent de-duplication
- [ ] Validation and source/target gap analysis
- [ ] Robustness and graceful error handling
- [ ] Command-line interface and synthetic sample files
- [ ] Continuous integration

## License

MIT