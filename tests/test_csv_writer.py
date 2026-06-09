"""Tests for the CSV writer."""

import csv
from fix_alloc.model import AllocationInstruction, Allocation, Party
from fix_alloc.transform import flatten
from fix_alloc.csv_writer import write_csv
from fix_alloc.target_schema import TARGET_COLUMNS


def make_rows():
    instr = AllocationInstruction(
        alloc_id="ALLOC001",
        alloc_trans_type="0",
        side="1",
        symbol="AAPL",
        quantity="1000",
        allocations=[
            Allocation(account="ACCT1", quantity="600"),
            Allocation(account="ACCT2", quantity="400"),
        ],
        parties=[Party(party_id="BRKA", role=1)],
    )
    return flatten(instr)


class TestWriteCsv:
    def test_header_matches_schema(self, tmp_path):
        out = tmp_path / "out.csv"
        write_csv(make_rows(), str(out))

        with open(out, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        assert header == TARGET_COLUMNS

    def test_one_row_per_allocation(self, tmp_path):
        out = tmp_path / "out.csv"
        write_csv(make_rows(), str(out))

        with open(out, newline="", encoding="utf-8") as f:
            data_rows = list(csv.DictReader(f))
        assert len(data_rows) == 2

    def test_values_mapped_correctly(self, tmp_path):
        out = tmp_path / "out.csv"
        write_csv(make_rows(), str(out))

        with open(out, newline="", encoding="utf-8") as f:
            data_rows = list(csv.DictReader(f))
        assert data_rows[0]["symbol"] == "AAPL"
        assert data_rows[0]["alloc_account"] == "ACCT1"
        assert data_rows[0]["alloc_qty"] == "600"
        assert data_rows[0]["executing_firm"] == "BRKA"
        assert data_rows[1]["alloc_account"] == "ACCT2"