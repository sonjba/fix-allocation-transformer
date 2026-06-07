"""FIX wire parser: tokenizes and structures FIX messages."""

from typing import List, Tuple, Dict, Set
from dataclasses import dataclass
from fix_alloc import tags


class ParseError(Exception):
    """Raised when parsing fails."""
    pass


def tokenize(message: str) -> List[Tuple[int, str]]:
    """
    Tokenize a FIX message into (tag, value) pairs.
    
    FIX messages are sequences of tag=value pairs separated by SOH (0x01).
    
    Args:
        message: Raw FIX string (may contain SOH bytes)
        
    Returns:
        List of (tag, value) tuples in order
        
    Raises:
        ParseError: If message is malformed
    """
    if not message:
        raise ParseError("Empty message")
    
    # Split on SOH byte (0x01)
    fields = message.split('\x01')
    
    tokens = []
    for field in fields:
        if not field:  # Skip empty fields (e.g., trailing SOH)
            continue
        
        if '=' not in field:
            raise ParseError(f"Malformed field (no '='): {field}")
        
        tag_str, value = field.split('=', 1)
        
        try:
            tag = int(tag_str)
        except ValueError:
            raise ParseError(f"Invalid tag (not an integer): {tag_str}")
        
        tokens.append((tag, value))
    
    return tokens


@dataclass
class GroupSpec:
    """Describes the structure of a FIX repeating group."""
    count_tag: int        # tag announcing how many entries (e.g. 78 = NoAllocs)
    delimiter_tag: int    # tag marking the start of each entry (e.g. 79 = AllocAccount)
    member_tags: Set[int] # all tags belonging to one entry


# Concrete group specs for AllocationInstruction
ALLOCATIONS_GROUP = GroupSpec(
    count_tag=tags.NO_ALLOCS,            # 78
    delimiter_tag=tags.ALLOC_ACCOUNT,    # 79
    member_tags={
        tags.ALLOC_ACCOUNT,              # 79
        tags.ALLOC_QTY,                  # 80
        tags.ALLOC_PRICE,                # 366
        tags.INDIVIDUAL_ALLOC_ID,        # 467
    },
)

PARTIES_GROUP = GroupSpec(
    count_tag=tags.NO_PARTY_IDS,         # 453
    delimiter_tag=tags.PARTY_ID,         # 448
    member_tags={
        tags.PARTY_ID,                   # 448
        tags.PARTY_ID_SOURCE,            # 447
        tags.PARTY_ROLE,                 # 452
    },
)


def extract_group(
    tokens: List[Tuple[int, str]],
    spec: GroupSpec,
) -> Tuple[List[Dict[int, str]], int]:
    """
    Extract one repeating group from a flat token list.

    Walks the tokens, using the spec's delimiter tag to mark where each
    entry starts. Stops when it hits a tag that doesn't belong to the group.

    Returns:
        (entries, declared_count)
          entries        — list of dicts, each {tag: value} for one entry
          declared_count — the count the message claims (from the count tag)
    """
    # 1. Find the count tag, and where the entries begin
    start_index = None
    declared_count = 0
    for i, (tag, value) in enumerate(tokens):
        if tag == spec.count_tag:
            declared_count = int(value)
            start_index = i + 1
            break

    # Group not present in this message
    if start_index is None:
        return [], 0

    # 2. Walk the entries
    entries = []
    current = None

    for tag, value in tokens[start_index:]:
        if tag == spec.delimiter_tag:
            # delimiter → a new entry begins
            if current is not None:
                entries.append(current)   # save the entry
            current = {tag: value}        # start a fresh one
        elif tag in spec.member_tags:
            # a field belonging to the current entry
            if current is not None:
                current[tag] = value
        else:
            # tag outside the group → the group has ended
            break

    # 3. Save the final entry (the loop never gets a chance to)
    if current is not None:
        entries.append(current)

    return entries, declared_count



def validate_group_count(
    entries: List[Dict[int, str]],
    declared_count: int,
    group_name: str,
) -> None:
    """
    Check that the number of entries found matches the declared count.

    The count tag (e.g. NoAllocs 78) states how many entries should follow.
    If the actual number differs, the message is suspect.

    Raises:
        ParseError: if actual entry count differs from declared_count
    """
    actual_count = len(entries)
    if actual_count != declared_count:
        raise ParseError(
            f"{group_name} count mismatch: "
            f"declared {declared_count}, found {actual_count}"
        )




def extract_header(tokens: List[Tuple[int, str]]) -> Dict[int, str]:
    """
    Extract and validate the FIX header.
    
    Header consists of: BeginString (8), BodyLength (9), MsgType (35).
    These must be the first three fields.
    
    Args:
        tokens: List of (tag, value) pairs
        
    Returns:
        Dict of header fields {tag: value}
        
    Raises:
        ParseError: If header is invalid
    """
    if len(tokens) < 3:
        raise ParseError("Message too short for header")
    
    header = {}
    expected_tags = [8, 9, 35]  # BeginString, BodyLength, MsgType
    
    for i, expected_tag in enumerate(expected_tags):
        tag, value = tokens[i]
        if tag != expected_tag:
            raise ParseError(f"Expected tag {expected_tag} at position {i}, got {tag}")
        header[tag] = value
    
    return header


def extract_trailer(tokens: List[Tuple[int, str]]) -> Dict[int, str]:
    """
    Extract the FIX trailer (CheckSum tag 10).
    
    CheckSum must be the last field.
    
    Args:
        tokens: List of (tag, value) pairs
        
    Returns:
        Dict with trailer fields {tag: value}
        
    Raises:
        ParseError: If trailer is invalid
    """
    if not tokens or tokens[-1][0] != 10:
        raise ParseError("Missing or invalid CheckSum (tag 10) as last field")
    
    return {tokens[-1][0]: tokens[-1][1]}


def parse_message(message: str) -> Dict:
    """
    Parse a FIX message into its components.
    
    Returns a dict with 'header', 'body', and 'trailer'.
    
    Args:
        message: Raw FIX string
        
    Returns:
        {
            'header': {tag: value, ...},
            'body': [(tag, value), ...],
            'trailer': {tag: value, ...}
        }
        
    Raises:
        ParseError: If message is malformed
    """
    tokens = tokenize(message)
    header = extract_header(tokens)
    trailer = extract_trailer(tokens)
    
    # Body is everything between header (first 3 fields) and trailer (last 1 field)
    body = tokens[3:-1]
    
    return {
        'header': header,
        'body': body,
        'trailer': trailer,
    }