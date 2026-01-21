"""
Smoke tests for field_validator.py - basic functionality validation with minimal external dependencies
"""

import pytest
from src.validation.field_validator import FieldValidator


class TestFieldValidatorSmoke:
    """Smoke tests for FieldValidator functionality"""

    def test_field_validator_class_exists(self):
        """Smoke test: FieldValidator class can be imported and instantiated"""
        # Class should exist and be accessible
        assert FieldValidator is not None
        assert hasattr(FieldValidator, 'validate_field')
        assert hasattr(FieldValidator, 'get_field_bounds')
        assert hasattr(FieldValidator, 'is_field_validatable')

    def test_constants_accessible(self):
        """Smoke test: class constants are accessible"""
        # All constants should be accessible
        assert hasattr(FieldValidator, 'FIELD_BOUNDS')
        assert hasattr(FieldValidator, 'NON_NEGATIVE_FIELDS')
        assert hasattr(FieldValidator, 'INT_FIELDS')

        # Constants should be dictionaries/lists
        assert isinstance(FieldValidator.FIELD_BOUNDS, dict)
        assert isinstance(FieldValidator.NON_NEGATIVE_FIELDS, list)
        assert isinstance(FieldValidator.INT_FIELDS, list)

        # Constants should not be empty
        assert len(FieldValidator.FIELD_BOUNDS) > 0
        assert len(FieldValidator.NON_NEGATIVE_FIELDS) > 0
        assert len(FieldValidator.INT_FIELDS) > 0

    def test_validate_field_basic_call(self):
        """Smoke test: validate_field can be called with basic parameters"""
        # Should not raise exceptions for basic calls
        result = FieldValidator.validate_field("energy", 50.0)
        assert isinstance(result, (int, float))

        result = FieldValidator.validate_field("ticks", 10)
        assert isinstance(result, int)

        result = FieldValidator.validate_field("fatigue", 5.0)
        assert isinstance(result, float)

    def test_validate_field_with_clamp(self):
        """Smoke test: validate_field works with clamp parameter"""
        # Should not raise exceptions
        result = FieldValidator.validate_field("energy", 50.0, clamp=True)
        assert isinstance(result, (int, float))

        result = FieldValidator.validate_field("energy", -10.0, clamp=True)
        assert isinstance(result, (int, float))

        result = FieldValidator.validate_field("ticks", -5, clamp=True)
        assert isinstance(result, int)

    def test_validate_field_common_fields(self):
        """Smoke test: validate_field works for common SelfState fields"""
        common_fields = [
            ("energy", 75.0),
            ("integrity", 0.8),
            ("stability", 0.6),
            ("fatigue", 20.0),
            ("tension", 15.0),
            ("ticks", 100),
            ("age", 50.0),
            ("subjective_time", 1000.0),
        ]

        for field_name, value in common_fields:
            result = FieldValidator.validate_field(field_name, value)
            assert isinstance(result, (int, float))

    def test_validate_field_clamp_common_scenarios(self):
        """Smoke test: validate_field clamping works for common scenarios"""
        # Test energy clamping
        assert FieldValidator.validate_field("energy", -5.0, clamp=True) == 0.0
        assert FieldValidator.validate_field("energy", 150.0, clamp=True) == 100.0

        # Test integrity clamping
        assert FieldValidator.validate_field("integrity", -0.1, clamp=True) == 0.0
        assert FieldValidator.validate_field("integrity", 1.5, clamp=True) == 1.0

        # Test non-negative field clamping
        assert FieldValidator.validate_field("fatigue", -10.0, clamp=True) == 0.0
        assert FieldValidator.validate_field("tension", -5.0, clamp=True) == 0.0

        # Test int field clamping
        assert FieldValidator.validate_field("ticks", -1, clamp=True) == 0

    def test_get_field_bounds_basic(self):
        """Smoke test: get_field_bounds works"""
        # Should return tuple or None
        bounds = FieldValidator.get_field_bounds("energy")
        assert bounds is None or isinstance(bounds, tuple)

        bounds = FieldValidator.get_field_bounds("unknown_field")
        assert bounds is None

    def test_is_field_validatable_basic(self):
        """Smoke test: is_field_validatable works"""
        # Should return boolean
        assert isinstance(FieldValidator.is_field_validatable("energy"), bool)
        assert isinstance(FieldValidator.is_field_validatable("unknown"), bool)

        # Known fields should be validatable
        assert FieldValidator.is_field_validatable("energy") is True
        assert FieldValidator.is_field_validatable("fatigue") is True
        assert FieldValidator.is_field_validatable("ticks") is True

    def test_validate_field_error_handling(self):
        """Smoke test: validate_field handles errors gracefully when clamping"""
        # Should not raise when clamping
        result = FieldValidator.validate_field("energy", -100.0, clamp=True)
        assert isinstance(result, float)

        result = FieldValidator.validate_field("ticks", -50, clamp=True)
        assert isinstance(result, int)

        result = FieldValidator.validate_field("fatigue", -25.0, clamp=True)
        assert isinstance(result, float)

    def test_validate_field_type_coercion(self):
        """Smoke test: validate_field handles type coercion"""
        # Int input for float fields should work
        result = FieldValidator.validate_field("energy", 50)
        assert result == 50.0

        # Float input for int fields should be truncated
        result = FieldValidator.validate_field("ticks", 10.7)
        assert result == 10

    def test_validate_field_boundary_values(self):
        """Smoke test: validate_field handles boundary values"""
        # Exact boundary values should work
        assert FieldValidator.validate_field("energy", 0.0) == 0.0
        assert FieldValidator.validate_field("energy", 100.0) == 100.0
        assert FieldValidator.validate_field("integrity", 0.0) == 0.0
        assert FieldValidator.validate_field("integrity", 1.0) == 1.0
        assert FieldValidator.validate_field("ticks", 0) == 0

    def test_class_method_behavior(self):
        """Smoke test: class methods work as expected"""
        # Methods should be callable without instance
        result = FieldValidator.validate_field("energy", 50.0)
        assert result == 50.0

        bounds = FieldValidator.get_field_bounds("energy")
        assert bounds == (0.0, 100.0)

        validatable = FieldValidator.is_field_validatable("energy")
        assert validatable is True

    def test_constants_content_validation(self):
        """Smoke test: validate constants contain expected content"""
        # FIELD_BOUNDS should contain expected fields
        expected_bounded_fields = ["energy", "integrity", "stability"]
        for field in expected_bounded_fields:
            assert field in FieldValidator.FIELD_BOUNDS
            bounds = FieldValidator.FIELD_BOUNDS[field]
            assert len(bounds) == 2
            assert bounds[0] <= bounds[1]

        # NON_NEGATIVE_FIELDS should contain expected fields
        expected_non_neg_fields = ["fatigue", "tension", "age", "subjective_time"]
        for field in expected_non_neg_fields:
            assert field in FieldValidator.NON_NEGATIVE_FIELDS

        # INT_FIELDS should contain expected fields
        expected_int_fields = ["ticks", "clarity_duration"]
        for field in expected_int_fields:
            assert field in FieldValidator.INT_FIELDS

    def test_validate_field_unknown_field(self):
        """Smoke test: validate_field handles unknown fields"""
        # Should not raise for unknown fields
        result = FieldValidator.validate_field("unknown_field", 42.5)
        assert isinstance(result, float)
        assert result == 42.5

    def test_validate_field_precision(self):
        """Smoke test: validate_field preserves precision"""
        # Should preserve float precision
        test_value = 50.123456789
        result = FieldValidator.validate_field("energy", test_value)
        assert abs(result - test_value) < 1e-10

    def test_validate_field_int_fields_precision(self):
        """Smoke test: int fields properly truncate"""
        # Should truncate towards zero
        assert FieldValidator.validate_field("ticks", 5.9) == 5
        assert FieldValidator.validate_field("ticks", 5.1) == 5
        assert FieldValidator.validate_field("ticks", -0.9) == 0  # When clamped

    def test_validate_field_consistent_behavior(self):
        """Smoke test: validate_field behaves consistently"""
        # Multiple calls with same input should give same output
        for _ in range(5):
            result1 = FieldValidator.validate_field("energy", 50.0)
            result2 = FieldValidator.validate_field("energy", 50.0, clamp=True)
            result3 = FieldValidator.validate_field("fatigue", 10.0)
            result4 = FieldValidator.validate_field("ticks", 100)

            assert result1 == result2 == 50.0
            assert result3 == 10.0
            assert result4 == 100

    def test_utility_methods_consistent(self):
        """Smoke test: utility methods are consistent"""
        # is_field_validatable should match actual validation capability
        test_fields = ["energy", "fatigue", "ticks", "unknown_field"]

        for field in test_fields:
            is_validatable = FieldValidator.is_field_validatable(field)
            assert isinstance(is_validatable, bool)

            # If validatable, should have bounds or be in special lists
            if is_validatable:
                has_bounds = FieldValidator.get_field_bounds(field) is not None
                is_non_neg = field in FieldValidator.NON_NEGATIVE_FIELDS
                is_int = field in FieldValidator.INT_FIELDS
                assert has_bounds or is_non_neg or is_int

    def test_validate_field_no_side_effects(self):
        """Smoke test: validate_field has no side effects on class state"""
        # Store original state
        original_bounds = FieldValidator.FIELD_BOUNDS.copy()
        original_non_neg = FieldValidator.NON_NEGATIVE_FIELDS.copy()
        original_int = FieldValidator.INT_FIELDS.copy()

        # Perform various validations
        FieldValidator.validate_field("energy", 50.0)
        FieldValidator.validate_field("energy", -10.0, clamp=True)
        FieldValidator.validate_field("ticks", 100)
        FieldValidator.validate_field("unknown", 42.0)

        # Verify no changes to class state
        assert FieldValidator.FIELD_BOUNDS == original_bounds
        assert FieldValidator.NON_NEGATIVE_FIELDS == original_non_neg
        assert FieldValidator.INT_FIELDS == original_int