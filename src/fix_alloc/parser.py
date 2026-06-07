"""FIX wire parser: tokenizes and structures FIX messages."""

from typing import List, Tuple, Dict


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