"""Domain model for parsed FIX AllocationInstruction messages."""

from dataclasses import dataclass, field
from typing import List


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