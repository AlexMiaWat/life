"""
Static tests for security_utils.py - basic functionality validation
"""

import pytest
from src.security_utils import sanitize_for_logging


def test_sanitize_for_logging_string_no_sensitive():
    """Test sanitize_for_logging with string containing no sensitive data"""
    input_data = "This is a normal log message"
    result = sanitize_for_logging(input_data)
    assert result == input_data


def test_sanitize_for_logging_string_with_sensitive():
    """Test sanitize_for_logging with string containing sensitive data"""
    input_data = "Log message with api_key=secret123 and password=pass456"
    result = sanitize_for_logging(input_data)

    assert "api_key" not in result
    assert "password" not in result
    assert "***REDACTED***" in result


def test_sanitize_for_logging_dict_no_sensitive():
    """Test sanitize_for_logging with dict containing no sensitive data"""
    input_data = {"user": "john", "action": "login", "ip": "192.168.1.1"}
    result = sanitize_for_logging(input_data)

    assert result == input_data
    assert result["user"] == "john"


def test_sanitize_for_logging_dict_with_sensitive():
    """Test sanitize_for_logging with dict containing sensitive data"""
    input_data = {
        "user": "john",
        "api_key": "secret123",
        "password": "pass456",
        "token": "token789",
        "normal_field": "normal_value"
    }
    result = sanitize_for_logging(input_data)

    assert result["user"] == "john"
    assert result["normal_field"] == "normal_value"
    assert result["api_key"] == "***REDACTED*** (length: 9)"
    assert result["password"] == "***REDACTED*** (length: 8)"
    assert result["token"] == "***REDACTED*** (length: 8)"


def test_sanitize_for_logging_list():
    """Test sanitize_for_logging with list"""
    input_data = [
        "normal_item",
        {"api_key": "secret"},
        "another_normal"
    ]
    result = sanitize_for_logging(input_data)

    assert result[0] == "normal_item"
    assert result[2] == "another_normal"
    assert result[1]["api_key"] == "***REDACTED*** (length: 6)"


def test_sanitize_for_logging_nested_structures():
    """Test sanitize_for_logging with nested data structures"""
    input_data = {
        "user": {
            "name": "john",
            "credentials": {
                "password": "secret",
                "api_key": "key123"
            }
        },
        "session": {
            "token": "session_token",
            "data": ["item1", {"secret": "hidden"}]
        }
    }
    result = sanitize_for_logging(input_data)

    # Check nested sensitive data is redacted
    assert result["user"]["credentials"]["password"] == "***REDACTED*** (length: 6)"
    assert result["user"]["credentials"]["api_key"] == "***REDACTED*** (length: 6)"
    assert result["session"]["token"] == "***REDACTED*** (length: 12)"

    # Check non-sensitive data is preserved
    assert result["user"]["name"] == "john"
    assert result["session"]["data"][0] == "item1"
    assert result["session"]["data"][1]["secret"] == "***REDACTED*** (length: 6)"


def test_sanitize_for_logging_non_string_values():
    """Test sanitize_for_logging with non-string sensitive values"""
    input_data = {
        "api_key": 12345,  # Number
        "password": ["a", "b", "c"],  # List
        "token": {"key": "value"},  # Dict
        "normal": "value"
    }
    result = sanitize_for_logging(input_data)

    assert result["normal"] == "value"
    assert result["api_key"] == "***REDACTED***"
    assert result["password"] == "***REDACTED***"
    assert result["token"] == "***REDACTED***"


def test_sanitize_for_logging_case_insensitive():
    """Test sanitize_for_logging is case insensitive"""
    input_data = {
        "API_KEY": "secret",
        "Password": "pass",
        "TOKEN": "token123",
        "normal": "value"
    }
    result = sanitize_for_logging(input_data)

    assert result["normal"] == "value"
    assert result["API_KEY"] == "***REDACTED*** (length: 6)"
    assert result["Password"] == "***REDACTED*** (length: 4)"
    assert result["TOKEN"] == "***REDACTED*** (length: 8)"


def test_sanitize_for_logging_various_sensitive_keywords():
    """Test sanitize_for_logging detects various sensitive keywords"""
    sensitive_keywords = [
        'api_key', 'apikey', 'api-key',
        'password', 'passwd', 'pwd',
        'token', 'secret', 'secret_key',
        'access_token', 'refresh_token',
        'auth', 'authorization',
        'credential', 'credentials',
        'private_key', 'privatekey',
        'session_id', 'sessionid',
        'bearer'
    ]

    for keyword in sensitive_keywords:
        input_data = {keyword: "sensitive_value"}
        result = sanitize_for_logging(input_data)
        assert result[keyword] == "***REDACTED*** (length: 15)"


def test_sanitize_for_logging_empty_structures():
    """Test sanitize_for_logging with empty structures"""
    assert sanitize_for_logging("") == ""
    assert sanitize_for_logging([]) == []
    assert sanitize_for_logging({}) == {}


def test_sanitize_for_logging_none_and_other_types():
    """Test sanitize_for_logging with None and other types"""
    assert sanitize_for_logging(None) is None
    assert sanitize_for_logging(42) == 42
    assert sanitize_for_logging(3.14) == 3.14
    assert sanitize_for_logging(True) is True


def test_sanitize_for_logging_preserves_structure():
    """Test sanitize_for_logging preserves data structure"""
    input_data = {
        "list": [1, {"password": "secret"}, 3],
        "dict": {"nested": {"token": "value"}},
        "string": "normal text"
    }
    result = sanitize_for_logging(input_data)

    # Structure should be preserved
    assert isinstance(result["list"], list)
    assert len(result["list"]) == 3
    assert isinstance(result["dict"], dict)
    assert isinstance(result["dict"]["nested"], dict)

    # Sensitive data should be redacted
    assert result["list"][1]["password"] == "***REDACTED*** (length: 6)"
    assert result["dict"]["nested"]["token"] == "***REDACTED*** (length: 5)"

    # Non-sensitive data should be preserved
    assert result["list"][0] == 1
    assert result["list"][2] == 3
    assert result["string"] == "normal text"


def test_sanitize_for_logging_no_modification_of_original():
    """Test sanitize_for_logging doesn't modify original data"""
    original = {
        "api_key": "secret",
        "normal": "value",
        "nested": {"password": "pass"}
    }
    original_copy = original.copy()

    result = sanitize_for_logging(original)

    # Original should be unchanged
    assert original == original_copy
    assert original["api_key"] == "secret"
    assert original["nested"]["password"] == "pass"

    # Result should be different
    assert result != original
    assert result["api_key"] != original["api_key"]