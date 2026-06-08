"""Unit tests for the FIX parser."""

import pytest
from fix_alloc.parser import tokenize, extract_header, extract_trailer, parse_message, ParseError


from fix_alloc.parser import (
    tokenize, extract_header, extract_trailer, parse_message, ParseError,
    extract_group, validate_group_count, parse_allocation_instruction,
    ALLOCATIONS_GROUP, PARTIES_GROUP,
)

class TestTokenize:
    """Test the tokenizer."""
    
    def test_clean_message(self):
        """Parse a clean FIX message."""
        msg = "8=FIX.4.4\x0135=J\x0149=SENDER\x0110=123\x01"
        tokens = tokenize(msg)
        
        assert len(tokens) == 4
        assert tokens[0] == (8, "FIX.4.4")
        assert tokens[1] == (35, "J")
        assert tokens[2] == (49, "SENDER")
        assert tokens[3] == (10, "123")
    
    def test_trailing_soh(self):
        """Handle trailing SOH correctly."""
        msg = "8=FIX.4.4\x0135=J\x01"
        tokens = tokenize(msg)
        
        # Should have 2 tokens, skipping empty field after trailing SOH
        assert len(tokens) == 2
        assert tokens[0] == (8, "FIX.4.4")
        assert tokens[1] == (35, "J")
    
    def test_missing_equals(self):
        """Reject field without '=' separator."""
        msg = "8FIX.4.4\x01"
        
        with pytest.raises(ParseError, match="Malformed field"):
            tokenize(msg)
    
    def test_invalid_tag(self):
        """Reject non-numeric tag."""
        msg = "abc=value\x01"
        
        with pytest.raises(ParseError, match="Invalid tag"):
            tokenize(msg)
    
    def test_empty_message(self):
        """Reject empty message."""
        with pytest.raises(ParseError, match="Empty message"):
            tokenize("")


class TestExtractHeader:
    """Test header extraction."""
    
    def test_valid_header(self):
        """Extract valid header."""
        tokens = [(8, "FIX.4.4"), (9, "100"), (35, "J"), (49, "SENDER")]
        header = extract_header(tokens)
        
        assert header[8] == "FIX.4.4"
        assert header[9] == "100"
        assert header[35] == "J"
    
    def test_header_too_short(self):
        """Reject message shorter than header."""
        tokens = [(8, "FIX.4.4")]
        
        with pytest.raises(ParseError, match="too short"):
            extract_header(tokens)
    
    def test_wrong_tag_order(self):
        """Reject wrong tag order in header."""
        tokens = [(8, "FIX.4.4"), (35, "J"), (9, "100")]  # 35 before 9
        
        with pytest.raises(ParseError, match="Expected tag"):
            extract_header(tokens)


class TestExtractTrailer:
    """Test trailer extraction."""
    
    def test_valid_trailer(self):
        """Extract valid trailer."""
        tokens = [(8, "FIX.4.4"), (35, "J"), (10, "123")]
        trailer = extract_trailer(tokens)
        
        assert trailer[10] == "123"
    
    def test_missing_checksum(self):
        """Reject message without CheckSum."""
        tokens = [(8, "FIX.4.4"), (35, "J")]
        
        with pytest.raises(ParseError, match="Missing"):
            extract_trailer(tokens)
    
    def test_wrong_last_tag(self):
        """Reject if last tag is not CheckSum."""
        tokens = [(8, "FIX.4.4"), (35, "J"), (49, "SENDER")]
        
        with pytest.raises(ParseError, match="invalid CheckSum"):
            extract_trailer(tokens)


class TestParseMessage:
    """Test full message parsing."""
    
    def test_simple_message(self):
        """Parse a simple valid message."""
        msg = "8=FIX.4.4\x019=50\x0135=J\x0149=SENDER\x0156=TARGET\x0170=ALLOC123\x0110=000\x01"
        result = parse_message(msg)
        
        assert result['header'][8] == "FIX.4.4"
        assert result['header'][35] == "J"
        assert result['header'][9] == "50"
        assert result['trailer'][10] == "000"
        
        # Body should contain middle fields (not header, not trailer)
        body_tags = [tag for tag, _ in result['body']]
        assert 49 in body_tags
        assert 56 in body_tags
        assert 70 in body_tags
    
    def test_malformed_message(self):
        """Reject malformed message."""
        msg = "8=FIX.4.4\x01GARBAGE\x0110=000\x01"
        
        with pytest.raises(ParseError):
            parse_message(msg)


class TestExtractGroup:
    """Test repeating-group extraction."""

    def test_single_allocation(self):
        """One allocation entry."""
        tokens = [(78, "1"), (79, "ACCT1"), (80, "600"), (467, "IND1")]
        entries, count = extract_group(tokens, ALLOCATIONS_GROUP)

        assert count == 1
        assert len(entries) == 1
        assert entries[0] == {79: "ACCT1", 80: "600", 467: "IND1"}

    def test_multiple_allocations(self):
        """Two allocation entries, split correctly on the delimiter."""
        tokens = [(78, "2"), (79, "ACCT1"), (80, "600"), (79, "ACCT2"), (80, "400")]
        entries, count = extract_group(tokens, ALLOCATIONS_GROUP)

        assert count == 2
        assert len(entries) == 2
        assert entries[0] == {79: "ACCT1", 80: "600"}
        assert entries[1] == {79: "ACCT2", 80: "400"}

    def test_multiple_parties(self):
        """Parties group uses a different spec (count 453, delimiter 448)."""
        tokens = [(453, "2"), (448, "BRK"), (452, "1"), (448, "CLR"), (452, "4")]
        entries, count = extract_group(tokens, PARTIES_GROUP)

        assert count == 2
        assert len(entries) == 2
        assert entries[0] == {448: "BRK", 452: "1"}
        assert entries[1] == {448: "CLR", 452: "4"}

    def test_empty_group_count_zero(self):
        """Count tag present but zero — no entries, stops at next section."""
        tokens = [(78, "0"), (453, "1"), (448, "BRK"), (452, "1")]
        entries, count = extract_group(tokens, ALLOCATIONS_GROUP)

        assert count == 0
        assert entries == []

    def test_group_not_present(self):
        """No count tag at all — group absent."""
        tokens = [(54, "1"), (55, "AAPL")]
        entries, count = extract_group(tokens, ALLOCATIONS_GROUP)

        assert count == 0
        assert entries == []


class TestGroupCountValidation:
    """Test count-mismatch detection."""

    def test_count_mismatch_raises(self):
        """Declared 3, only 2 present → must raise."""
        tokens = [(78, "3"), (79, "ACCT1"), (80, "600"), (79, "ACCT2"), (80, "400")]
        entries, count = extract_group(tokens, ALLOCATIONS_GROUP)

        assert len(entries) == 2  # actual
        assert count == 3         # declared

        with pytest.raises(ParseError, match="count mismatch"):
            validate_group_count(entries, count, "Allocations")

    def test_count_matches_passes(self):
        """Declared count matches actual → no error."""
        entries = [{79: "ACCT1"}, {79: "ACCT2"}]
        # Should not raise:
        validate_group_count(entries, 2, "Allocations")


class TestParseAllocationInstruction:
    """Full end-to-end parse of a complete message."""

    def test_parse_full_message(self):
        """A complete multi-account message parses into structured data."""
        msg = (
            "8=FIX.4.4\x019=NN\x0135=J\x0149=BROKER\x0156=BUYSIDE\x01"
            "70=ALLOC001\x0171=0\x0154=1\x0155=AAPL\x0153=1000\x01"
            "78=2\x0179=ACCT1\x0180=600\x0179=ACCT2\x0180=400\x01"
            "453=2\x01448=BRK\x01452=1\x01448=CLR\x01452=4\x01"
            "10=000\x01"
        )
        result = parse_allocation_instruction(msg)

        # Header
        assert result["header"][35] == "J"

        # Trade-level fields
        assert result["trade"][70] == "ALLOC001"
        assert result["trade"][55] == "AAPL"
        assert result["trade"][53] == "1000"

        # Allocations
        assert len(result["allocations"]) == 2
        assert result["allocations"][0] == {79: "ACCT1", 80: "600"}
        assert result["allocations"][1] == {79: "ACCT2", 80: "400"}

        # Parties
        assert len(result["parties"]) == 2
        assert result["parties"][0] == {448: "BRK", 452: "1"}
        assert result["parties"][1] == {448: "CLR", 452: "4"}

        # Trailer
        assert result["trailer"][10] == "000"