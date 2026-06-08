"""Resolve FIX parties into named role columns."""

from typing import List, Dict
from fix_alloc import tags
from fix_alloc.model import Party


# Maps a PartyRole code to its target CSV column name.
ROLE_TO_COLUMN = {
    tags.PARTY_ROLE_EXECUTING_FIRM:       "executing_firm",        # 1
    tags.PARTY_ROLE_CLIENT_ID:            "client_id",             # 3
    tags.PARTY_ROLE_CLEARING_FIRM:        "clearing_firm",         # 4
    tags.PARTY_ROLE_INVESTOR_ID:          "investor_id",           # 5
    tags.PARTY_ROLE_INTRODUCING_FIRM:     "introducing_firm",      # 6
    tags.PARTY_ROLE_ORDER_ORIGIN_FIRM:    "order_origin_firm",     # 13
    tags.PARTY_ROLE_GIVEUP_CLEARING_FIRM: "giveup_clearing_firm",  # 14
}


def build_role_map(parties: List[Party]) -> Dict[int, List[str]]:
    """
    Group party IDs by their role.

    Returns:
        {role_code: [party_id, ...]} — a role may map to more than one ID.
    """
    role_map: Dict[int, List[str]] = {}
    for party in parties:
        role_map.setdefault(party.role, []).append(party.party_id)
    return role_map


def resolve_parties(parties: List[Party]) -> Dict[str, str]:
    """
    Resolve a list of parties into named target columns.

    Design decisions:
      - Missing role          -> column is left blank ("").
      - Role appears > once    -> the FIRST party ID is used.
        (Deliberate choice; the alternative would be to join them.)

    Returns:
        {column_name: party_id_or_blank} for every target column.
    """
    role_map = build_role_map(parties)

    resolved = {}
    for role, column in ROLE_TO_COLUMN.items():
        ids = role_map.get(role, [])
        resolved[column] = ids[0] if ids else ""
    return resolved