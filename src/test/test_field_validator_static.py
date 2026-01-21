"""
Static tests for field_validator.py - basic functionality validation without external dependencies
"""

import pytest
from src.validation.field_validator import FieldValidator


# Test class constants
def test_field_bounds_constant():
    """Test FIELD_BOUNDS constant structure"""
    bounds = FieldValidator.FIELD_BOUNDS

    # Check expected fields are present
    expected_fields = [
        "energy", "integrity", "stability",
        "last_event_intensity", "subjective_time_intensity_smoothing"
    ]

    for field in expected_fields:
        assert field in bounds
        assert isinstance(bounds[field], tuple)
        assert len(bounds[field]) == 2
        min_val, max_val = bounds[field]
        assert isinstance(min_val, float)
        assert isinstance(max_val, float)
        assert min_val <= max_val


def test_non_negative_fields_constant():
    """Test NON_NEGATIVE_FIELDS constant"""
    fields = FieldValidator.NON_NEGATIVE_FIELDS

    expected_fields = [
        "fatigue", "tension", "age", "subjective_time",
        "subjective_time_base_rate", "subjective_time_rate_min", "subjective_time_rate_max"
    ]

    assert set(fields) == set(expected_fields)
    assert all(isinstance(field, str) for field in fields)


def test_int_fields_constant():
    """Test INT_FIELDS constant"""
    fields = FieldValidator.INT_FIELDS

    expected_fields = ["ticks", "clarity_duration"]

    assert set(fields) == set(expected_fields)
    assert all(isinstance(field, str) for field in fields)


# Test validate_field method - bounded fields
def test_validate_field_energy_valid():
    """Test validate_field for energy field with valid values"""
    # Test valid values
    assert FieldValidator.validate_field("energy", 50.0) == 50.0
    assert FieldValidator.validate_field("energy", 0.0) == 0.0
    assert FieldValidator.validate_field("energy", 100.0) == 100.0


def test_validate_field_energy_invalid_no_clamp():
    """Test validate_field for energy field with invalid values (no clamp)"""
    # Test below minimum
    with pytest.raises(ValueError, match="energy must be between 0.0 and 100.0"):
        FieldValidator.validate_field("energy", -10.0)

    # Test above maximum
    with pytest.raises(ValueError, match="energy must be between 0.0 and 100.0"):
        FieldValidator.validate_field("energy", 150.0)


def test_validate_field_energy_clamp():
    """Test validate_field for energy field with clamping"""
    # Test clamping below minimum
    assert FieldValidator.validate_field("energy", -10.0, clamp=True) == 0.0

    # Test clamping above maximum
    assert FieldValidator.validate_field("energy", 150.0, clamp=True) == 100.0

    # Test valid values unchanged
    assert FieldValidator.validate_field("energy", 50.0, clamp=True) == 50.0


def test_validate_field_integrity_valid():
    """Test validate_field for integrity field with valid values"""
    assert FieldValidator.validate_field("integrity", 0.5) == 0.5
    assert FieldValidator.validate_field("integrity", 0.0) == 0.0
    assert FieldValidator.validate_field("integrity", 1.0) == 1.0


def test_validate_field_integrity_invalid_no_clamp():
    """Test validate_field for integrity field with invalid values (no clamp)"""
    with pytest.raises(ValueError, match="integrity must be between 0.0 and 1.0"):
        FieldValidator.validate_field("integrity", -0.1)

    with pytest.raises(ValueError, match="integrity must be between 0.0 and 1.0"):
        FieldValidator.validate_field("integrity", 1.5)


def test_validate_field_stability_valid():
    """Test validate_field for stability field with valid values"""
    assert FieldValidator.validate_field("stability", 0.3) == 0.3
    assert FieldValidator.validate_field("stability", 0.0) == 0.0
    assert FieldValidator.validate_field("stability", 1.0) == 1.0


def test_validate_field_stability_clamp():
    """Test validate_field for stability field with clamping"""
    assert FieldValidator.validate_field("stability", -0.2, clamp=True) == 0.0
    assert FieldValidator.validate_field("stability", 1.3, clamp=True) == 1.0


# Test validate_field method - non-negative fields
def test_validate_field_fatigue_valid():
    """Test validate_field for fatigue field with valid values"""
    assert FieldValidator.validate_field("fatigue", 0.0) == 0.0
    assert FieldValidator.validate_field("fatigue", 10.5) == 10.5
    assert FieldValidator.validate_field("fatigue", 100.0) == 100.0


def test_validate_field_fatigue_invalid_no_clamp():
    """Test validate_field for fatigue field with invalid values (no clamp)"""
    with pytest.raises(ValueError, match="fatigue must be >= 0.0"):
        FieldValidator.validate_field("fatigue", -5.0)


def test_validate_field_fatigue_clamp():
    """Test validate_field for fatigue field with clamping"""
    assert FieldValidator.validate_field("fatigue", -5.0, clamp=True) == 0.0
    assert FieldValidator.validate_field("fatigue", 10.0, clamp=True) == 10.0


def test_validate_field_tension_valid():
    """Test validate_field for tension field with valid values"""
    assert FieldValidator.validate_field("tension", 0.0) == 0.0
    assert FieldValidator.validate_field("tension", 25.7) == 25.7


def test_validate_field_tension_invalid_no_clamp():
    """Test validate_field for tension field with invalid values (no clamp)"""
    with pytest.raises(ValueError, match="tension must be >= 0.0"):
        FieldValidator.validate_field("tension", -1.0)


def test_validate_field_age_valid():
    """Test validate_field for age field with valid values"""
    assert FieldValidator.validate_field("age", 0.0) == 0.0
    assert FieldValidator.validate_field("age", 123.45) == 123.45


def test_validate_field_subjective_time_valid():
    """Test validate_field for subjective_time field with valid values"""
    assert FieldValidator.validate_field("subjective_time", 0.0) == 0.0
    assert FieldValidator.validate_field("subjective_time", 1000.5) == 1000.5


def test_validate_field_subjective_time_clamp():
    """Test validate_field for subjective_time field with clamping"""
    assert FieldValidator.validate_field("subjective_time", -100.0, clamp=True) == 0.0


# Test validate_field method - int fields
def test_validate_field_ticks_valid():
    """Test validate_field for ticks field with valid values"""
    assert FieldValidator.validate_field("ticks", 0) == 0
    assert FieldValidator.validate_field("ticks", 100) == 100
    assert FieldValidator.validate_field("ticks", 50.7) == 50  # Should convert to int


def test_validate_field_ticks_invalid_no_clamp():
    """Test validate_field for ticks field with invalid values (no clamp)"""
    with pytest.raises(ValueError, match="ticks must be >= 0"):
        FieldValidator.validate_field("ticks", -5)


def test_validate_field_ticks_clamp():
    """Test validate_field for ticks field with clamping"""
    assert FieldValidator.validate_field("ticks", -5, clamp=True) == 0
    assert FieldValidator.validate_field("ticks", 10.9, clamp=True) == 10


def test_validate_field_ticks_type_error():
    """Test validate_field for ticks field with wrong type"""
    with pytest.raises(ValueError, match="ticks must be a number"):
        FieldValidator.validate_field("ticks", "not_a_number")


def test_validate_field_clarity_duration_valid():
    """Test validate_field for clarity_duration field with valid values"""
    assert FieldValidator.validate_field("clarity_duration", 0) == 0
    assert FieldValidator.validate_field("clarity_duration", 60) == 60


def test_validate_field_clarity_duration_invalid():
    """Test validate_field for clarity_duration field with invalid values"""
    with pytest.raises(ValueError, match="clarity_duration must be >= 0"):
        FieldValidator.validate_field("clarity_duration", -1)


# Test validate_field method - type validation
def test_validate_field_type_validation():
    """Test validate_field type validation for various fields"""
    # Test with string input (should fail for numeric fields)
    with pytest.raises(ValueError, match="must be a number"):
        FieldValidator.validate_field("energy", "not_a_number")

    with pytest.raises(ValueError, match="must be a number"):
        FieldValidator.validate_field("fatigue", "invalid")

    with pytest.raises(ValueError, match="must be a number"):
        FieldValidator.validate_field("ticks", [1, 2, 3])


# Test validate_field method - unknown fields
def test_validate_field_unknown_field():
    """Test validate_field for unknown fields"""
    # Unknown fields should be returned as float
    assert FieldValidator.validate_field("unknown_field", 42.5) == 42.5
    assert FieldValidator.validate_field("custom_field", -10.0) == -10.0


# Test get_field_bounds method
def test_get_field_bounds_known_fields():
    """Test get_field_bounds for known fields"""
    # Test bounded fields
    assert FieldValidator.get_field_bounds("energy") == (0.0, 100.0)
    assert FieldValidator.get_field_bounds("integrity") == (0.0, 1.0)
    assert FieldValidator.get_field_bounds("stability") == (0.0, 1.0)
    assert FieldValidator.get_field_bounds("last_event_intensity") == (0.0, 1.0)
    assert FieldValidator.get_field_bounds("subjective_time_intensity_smoothing") == (0.0, 1.0)


def test_get_field_bounds_unknown_fields():
    """Test get_field_bounds for unknown fields"""
    assert FieldValidator.get_field_bounds("unknown_field") is None
    assert FieldValidator.get_field_bounds("fatigue") is None  # Non-negative but not bounded
    assert FieldValidator.get_field_bounds("ticks") is None  # Int field


# Test is_field_validatable method
def test_is_field_validatable():
    """Test is_field_validatable method"""
    # Should return True for all validatable fields
    validatable_fields = (
        list(FieldValidator.FIELD_BOUNDS.keys()) +
        FieldValidator.NON_NEGATIVE_FIELDS +
        FieldValidator.INT_FIELDS
    )

    for field in validatable_fields:
        assert FieldValidator.is_field_validatable(field) is True

    # Should return False for unknown fields
    assert FieldValidator.is_field_validatable("unknown_field") is False
    assert FieldValidator.is_field_validatable("custom_property") is False


# Test edge cases
def test_validate_field_int_conversion():
    """Test that int fields properly convert float to int"""
    assert FieldValidator.validate_field("ticks", 5.7) == 5
    assert FieldValidator.validate_field("ticks", 5.0) == 5
    assert FieldValidator.validate_field("clarity_duration", 30.9) == 30


def test_validate_field_float_precision():
    """Test float precision handling"""
    # Test with very small decimals
    result = FieldValidator.validate_field("energy", 50.123456789)
    assert abs(result - 50.123456789) < 1e-10

    # Test boundary values
    assert FieldValidator.validate_field("integrity", 1e-10) == 1e-10
    assert FieldValidator.validate_field("stability", 0.999999999) == 0.999999999


def test_validate_field_clamp_boundary_values():
    """Test clamping at exact boundary values"""
    # At exact boundaries - should not change
    assert FieldValidator.validate_field("energy", 0.0, clamp=True) == 0.0
    assert FieldValidator.validate_field("energy", 100.0, clamp=True) == 100.0
    assert FieldValidator.validate_field("integrity", 1.0, clamp=True) == 1.0

    # Just outside boundaries - should clamp
    assert FieldValidator.validate_field("energy", -0.0001, clamp=True) == 0.0
    assert FieldValidator.validate_field("energy", 100.0001, clamp=True) == 100.0


def test_validate_field_int_field_clamp_precision():
    """Test int field clamping precision"""
    # Negative values should clamp to 0
    assert FieldValidator.validate_field("ticks", -0.1, clamp=True) == 0
    assert FieldValidator.validate_field("ticks", -100, clamp=True) == 0

    # Float values should be truncated down
    assert FieldValidator.validate_field("ticks", 5.9, clamp=True) == 5
    assert FieldValidator.validate_field("ticks", 5.1, clamp=True) == 5


def test_validate_field_mixed_types():
    """Test validate_field with mixed input types that are valid"""
    # Test int input for float fields (should work)
    assert FieldValidator.validate_field("energy", 50) == 50.0
    assert FieldValidator.validate_field("fatigue", 10) == 10.0

    # Test float input for int fields (should convert)
    assert FieldValidator.validate_field("ticks", 5.0) == 5


# Test class method behavior
def test_class_methods_are_classmethods():
    """Test that methods are properly decorated as classmethods"""
    import inspect

    assert isinstance(inspect.getattr_static(FieldValidator, 'validate_field'), classmethod)
    assert isinstance(inspect.getattr_static(FieldValidator, 'get_field_bounds'), classmethod)
    assert isinstance(inspect.getattr_static(FieldValidator, 'is_field_validatable'), classmethod)


# Test constants immutability (attempt to modify should not affect original)
def test_constants_immutability():
    """Test that class constants cannot be modified externally"""
    # Store original values
    original_bounds = FieldValidator.FIELD_BOUNDS.copy()
    original_non_neg = FieldValidator.NON_NEGATIVE_FIELDS.copy()
    original_int_fields = FieldValidator.INT_FIELDS.copy()

    # Attempt to modify (this should not affect the class)
    try:
        FieldValidator.FIELD_BOUNDS["test"] = (0, 1)
        FieldValidator.NON_NEGATIVE_FIELDS.append("test")
        FieldValidator.INT_FIELDS.append("test")
    except Exception:
        pass  # Some implementations may prevent modification

    # Verify original values are unchanged
    assert FieldValidator.FIELD_BOUNDS == original_bounds
    assert FieldValidator.NON_NEGATIVE_FIELDS == original_non_neg
    assert FieldValidator.INT_FIELDS == original_int_fields