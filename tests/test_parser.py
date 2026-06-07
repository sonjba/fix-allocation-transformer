"""Unit tests for the FIX parser."""

import pytest
from fix_alloc.parser import tokenize, extract_header, extract_trailer, parse_message, ParseError


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