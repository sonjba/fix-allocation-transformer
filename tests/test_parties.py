"""Tests for party resolution."""

from fix_alloc.model import Party
from fix_alloc.parties import build_role_map, resolve_parties


class TestResolveParties:
    """Resolve parties into named columns."""

    def test_giveup_scenario(self):
        """Executing firm and giveup clearing firm stay in SEPARATE columns."""
        parties = [
            Party(party_id="BRKA", role=1),     # Executing Firm
            Party(party_id="BRKB", role=14),    # Giveup Clearing Firm
            Party(party_id="CLIENT1", role=3),  # Client ID
        ]
        resolved = resolve_parties(parties)

        assert resolved["executing_firm"] == "BRKA"
        assert resolved["giveup_clearing_firm"] == "BRKB"
        assert resolved["client_id"] == "CLIENT1"
        assert resolved["clearing_firm"] == ""   # role 4 absent

    def test_missing_role_is_blank(self):
        """A role that isn't present resolves to a blank column."""
        parties = [Party(party_id="BRKA", role=1)]  # only executing firm
        resolved = resolve_parties(parties)

        assert resolved["executing_firm"] == "BRKA"
        assert resolved["clearing_firm"] == ""
        assert resolved["investor_id"] == ""
        assert resolved["giveup_clearing_firm"] == ""

    def test_duplicate_role_uses_first(self):
        """When a role repeats, the first party ID wins (documented choice)."""
        parties = [
            Party(party_id="FIRST", role=1),
            Party(party_id="SECOND", role=1),
        ]
        resolved = resolve_parties(parties)

        assert resolved["executing_firm"] == "FIRST"

    def test_empty_parties(self):
        """No parties -> every column blank."""
        resolved = resolve_parties([])

        assert resolved["executing_firm"] == ""
        assert resolved["clearing_firm"] == ""


class TestBuildRoleMap:
    """Grouping party IDs by role."""

    def test_groups_by_role(self):
        parties = [
            Party(party_id="A", role=1),
            Party(party_id="B", role=1),
            Party(party_id="C", role=4),
        ]
        role_map = build_role_map(parties)

        assert role_map[1] == ["A", "B"]
        assert role_map[4] == ["C"]