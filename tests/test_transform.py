"""Tests for flattening and deduplication."""

from fix_alloc.model import AllocationInstruction, Allocation, Party
from fix_alloc.transform import flatten, deduplicate


def make_instruction(allocations):
    """An instruction with given allocations and a give-up party set."""
    return AllocationInstruction(
        alloc_id="ALLOC001",
        alloc_trans_type="0",
        side="1",
        symbol="AAPL",
        quantity="1000",
        allocations=allocations,
        parties=[
            Party(party_id="BRKA", role=1),    # executing firm
            Party(party_id="BRKB", role=14),   # giveup clearing firm
        ],
    )


class TestFlatten:
    def test_single_allocation_one_row(self):
        instr = make_instruction([Allocation(account="ACCT1", quantity="1000")])
        assert len(flatten(instr)) == 1

    def test_multiple_allocations_n_rows(self):
        instr = make_instruction([
            Allocation(account="ACCT1", quantity="600"),
            Allocation(account="ACCT2", quantity="400"),
        ])
        assert len(flatten(instr)) == 2

    def test_trade_fields_repeat(self):
        instr = make_instruction([
            Allocation(account="ACCT1", quantity="600"),
            Allocation(account="ACCT2", quantity="400"),
        ])
        rows = flatten(instr)
        assert rows[0]["symbol"] == "AAPL"
        assert rows[1]["symbol"] == "AAPL"
        assert rows[0]["trade_quantity"] == "1000"
        assert rows[1]["trade_quantity"] == "1000"

    def test_allocation_fields_vary(self):
        instr = make_instruction([
            Allocation(account="ACCT1", quantity="600"),
            Allocation(account="ACCT2", quantity="400"),
        ])
        rows = flatten(instr)
        assert rows[0]["alloc_account"] == "ACCT1"
        assert rows[0]["alloc_qty"] == "600"
        assert rows[1]["alloc_account"] == "ACCT2"
        assert rows[1]["alloc_qty"] == "400"

    def test_parties_merged(self):
        instr = make_instruction([Allocation(account="ACCT1", quantity="1000")])
        rows = flatten(instr)
        assert rows[0]["executing_firm"] == "BRKA"
        assert rows[0]["giveup_clearing_firm"] == "BRKB"
        assert rows[0]["clearing_firm"] == ""  # absent role


class TestDeduplicate:
    def test_removes_duplicates_on_reprocess(self):
        instr = make_instruction([
            Allocation(account="ACCT1", quantity="600"),
            Allocation(account="ACCT2", quantity="400"),
        ])
        rows = flatten(instr)
        doubled = rows + rows  # same message processed twice
        assert len(deduplicate(doubled)) == 2

    def test_keeps_distinct_allocations(self):
        instr = make_instruction([
            Allocation(account="ACCT1", quantity="600"),
            Allocation(account="ACCT2", quantity="400"),
        ])
        rows = flatten(instr)
        assert len(deduplicate(rows)) == 2