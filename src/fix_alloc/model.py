"""Domain model for parsed FIX AllocationInstruction messages."""

from dataclasses import dataclass, field
from typing import List, Dict
from fix_alloc import tags


@dataclass
class Party:
    """A single party from the Parties repeating group."""
    party_id: str
    role: int                  # PartyRole code (e.g. 1 = Executing Firm)
    party_id_source: str = ""


@dataclass
class Allocation:
    """A single account allocation from the NoAllocs repeating group."""
    account: str
    quantity: str
    price: str = ""
    individual_alloc_id: str = ""


@dataclass
class AllocationInstruction:
    """A full FIX AllocationInstruction as a clean domain object."""
    alloc_id: str
    alloc_trans_type: str
    side: str
    symbol: str
    quantity: str
    allocations: List[Allocation] = field(default_factory=list) # creates a fresh list for each instance
    parties: List[Party] = field(default_factory=list) # creates a fresh list for each instance


def build_instruction(parsed: Dict) -> AllocationInstruction:
    """
    Build a domain AllocationInstruction from a parsed dict.

    Translates the tag-keyed dicts produced by the parser into clean,
    named domain objects. This is the boundary between the FIX wire
    format and the domain model.
    """
    trade = parsed["trade"]

    allocations = [
        Allocation(
            account=alloc.get(tags.ALLOC_ACCOUNT, ""),
            quantity=alloc.get(tags.ALLOC_QTY, ""),
            price=alloc.get(tags.ALLOC_PRICE, ""),
            individual_alloc_id=alloc.get(tags.INDIVIDUAL_ALLOC_ID, ""),
        )
        for alloc in parsed["allocations"]
    ]

    parties = [
        Party(
            party_id=p.get(tags.PARTY_ID, ""),
            role=int(p.get(tags.PARTY_ROLE, "0")),
            party_id_source=p.get(tags.PARTY_ID_SOURCE, ""),
        )
        for p in parsed["parties"]
    ]

    return AllocationInstruction(
        alloc_id=trade.get(tags.ALLOC_ID, ""),
        alloc_trans_type=trade.get(tags.ALLOC_TRANS_TYPE, ""),
        side=trade.get(tags.SIDE, ""),
        symbol=trade.get(tags.SYMBOL, ""),
        quantity=trade.get(tags.QUANTITY, ""),
        allocations=allocations,
        parties=parties,
    )