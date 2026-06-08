"""Tests for the domain model builder."""

from fix_alloc.model import build_instruction, AllocationInstruction
from fix_alloc.parties import resolve_parties


def make_parsed():
    """A parsed dict, as parse_allocation_instruction would return."""
    return {
        "header": {35: "J"},
        "trade": {70: "ALLOC001", 71: "0", 54: "1", 55: "AAPL", 53: "1000"},
        "allocations": [
            {79: "ACCT1", 80: "600"},
            {79: "ACCT2", 80: "400"},
        ],
        "parties": [
            {448: "BRKA", 452: "1"},
            {448: "BRKB", 452: "14"},
        ],
        "trailer": {10: "000"},
    }


class TestBuildInstruction:
    """Building a domain object from a parsed dict."""

    def test_builds_top_level_fields(self):
        instr = build_instruction(make_parsed())

        assert isinstance(instr, AllocationInstruction)
        assert instr.alloc_id == "ALLOC001"
        assert instr.symbol == "AAPL"
        assert instr.quantity == "1000"

    def test_builds_allocations(self):
        instr = build_instruction(make_parsed())

        assert len(instr.allocations) == 2
        assert instr.allocations[0].account == "ACCT1"
        assert instr.allocations[0].quantity == "600"
        assert instr.allocations[1].account == "ACCT2"

    def test_converts_role_to_int(self):
        instr = build_instruction(make_parsed())

        assert instr.parties[0].party_id == "BRKA"
        assert instr.parties[0].role == 1     # string "1" -> int 1
        assert instr.parties[1].role == 14    # string "14" -> int 14

    def test_full_flow_resolves_parties(self):
        """End to end: parsed dict -> domain object -> resolved parties."""
        instr = build_instruction(make_parsed())
        resolved = resolve_parties(instr.parties)

        assert resolved["executing_firm"] == "BRKA"
        assert resolved["giveup_clearing_firm"] == "BRKB"