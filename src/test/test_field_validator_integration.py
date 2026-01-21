"""
Integration tests for field_validator.py - testing with real system components
"""

import pytest
from src.validation.field_validator import FieldValidator


class TestFieldValidatorIntegration:
    """Integration tests for FieldValidator with system components"""

    def test_field_validator_with_self_state_fields(self):
        """Integration test: validate_field works with typical SelfState field values"""
        # Test typical SelfState field values that would be used in the system
        test_cases = [
            # (field_name, valid_value, expected_result)
            ("energy", 85.5, 85.5),
            ("integrity", 0.95, 0.95),
            ("stability", 0.7, 0.7),
            ("fatigue", 12.3, 12.3),
            ("tension", 8.9, 8.9),
            ("ticks", 1500, 1500),
            ("age", 25.5, 25.5),
            ("subjective_time", 1234.56, 1234.56),
            ("last_event_intensity", 0.3, 0.3),
            ("subjective_time_intensity_smoothing", 0.8, 0.8),
            ("clarity_duration", 45, 45),
        ]

        for field_name, value, expected in test_cases:
            result = FieldValidator.validate_field(field_name, value)
            assert result == expected, f"Failed for field {field_name}"

    def test_field_validator_clamping_realistic_scenarios(self):
        """Integration test: clamping works for realistic out-of-bounds scenarios"""
        # Test scenarios that might occur in real system operation
        clamp_cases = [
            # Energy scenarios
            ("energy", -5.0, 0.0),      # Battery depleted
            ("energy", 120.0, 100.0),   # Overcharged
            ("energy", -0.001, 0.0),    # Slightly negative

            # Integrity scenarios
            ("integrity", -0.1, 0.0),   # Corrupted
            ("integrity", 1.2, 1.0),    # Perfect integrity exceeded
            ("integrity", -0.0001, 0.0), # Tiny corruption

            # Stability scenarios
            ("stability", -0.05, 0.0),  # Unstable
            ("stability", 1.1, 1.0),    # Over-stabilized

            # Non-negative field scenarios
            ("fatigue", -10.0, 0.0),    # Negative fatigue (impossible)
            ("tension", -1.0, 0.0),     # Negative tension
            ("age", -100.0, 0.0),       # Negative age
            ("subjective_time", -1.0, 0.0),  # Negative time

            # Int field scenarios
            ("ticks", -1, 0),           # Negative ticks
            ("clarity_duration", -5, 0), # Negative duration
        ]

        for field_name, input_value, expected in clamp_cases:
            result = FieldValidator.validate_field(field_name, input_value, clamp=True)
            assert result == expected, f"Clamping failed for {field_name}: {input_value} -> {result}, expected {expected}"

    def test_field_validator_error_scenarios(self):
        """Integration test: proper error handling for invalid inputs"""
        # Test scenarios that should raise errors in strict validation
        error_cases = [
            ("energy", -10.0, "energy must be between 0.0 and 100.0"),
            ("energy", 150.0, "energy must be between 0.0 and 100.0"),
            ("integrity", -0.5, "integrity must be between 0.0 and 1.0"),
            ("integrity", 2.0, "integrity must be between 0.0 and 1.0"),
            ("fatigue", -25.0, "fatigue must be >= 0.0"),
            ("ticks", -100, "ticks must be >= 0"),
            ("ticks", "not_a_number", "ticks must be a number"),
            ("energy", "invalid", "energy must be a number"),
        ]

        for field_name, value, expected_error in error_cases:
            with pytest.raises(ValueError, match=expected_error):
                FieldValidator.validate_field(field_name, value, clamp=False)

    def test_field_validator_type_coercion_integration(self):
        """Integration test: proper type coercion in realistic scenarios"""
        # Test type coercion that might occur when loading from different sources
        coercion_cases = [
            # (field_name, input_value, expected_output, expected_type)
            ("energy", 75, 75.0, float),           # int -> float
            ("fatigue", 10, 10.0, float),          # int -> float
            ("ticks", 100.0, 100, int),            # float -> int (truncation)
            ("ticks", 50.7, 50, int),              # float -> int (truncation)
            ("clarity_duration", 30.0, 30, int),   # float -> int
            ("subjective_time", 100, 100.0, float), # int -> float
        ]

        for field_name, input_val, expected_val, expected_type in coercion_cases:
            result = FieldValidator.validate_field(field_name, input_val)
            assert result == expected_val, f"Type coercion failed for {field_name}: {input_val} -> {result}"
            assert isinstance(result, expected_type), f"Wrong type for {field_name}: {type(result)}"

    def test_field_validator_bounds_integration(self):
        """Integration test: bounds checking integrates properly"""
        # Test that get_field_bounds and validate_field are consistent
        bounded_fields = FieldValidator.FIELD_BOUNDS.keys()

        for field_name in bounded_fields:
            bounds = FieldValidator.get_field_bounds(field_name)
            assert bounds is not None
            min_val, max_val = bounds

            # Test boundary values
            assert FieldValidator.validate_field(field_name, min_val) == min_val
            assert FieldValidator.validate_field(field_name, max_val) == max_val

            # Test clamping at boundaries
            assert FieldValidator.validate_field(field_name, min_val - 1, clamp=True) == min_val
            assert FieldValidator.validate_field(field_name, max_val + 1, clamp=True) == max_val

    def test_field_validator_validatable_fields_consistency(self):
        """Integration test: is_field_validatable consistency with actual validation"""
        # Test that all fields marked as validatable actually work with validate_field
        all_fields = (
            list(FieldValidator.FIELD_BOUNDS.keys()) +
            FieldValidator.NON_NEGATIVE_FIELDS +
            FieldValidator.INT_FIELDS
        )

        for field_name in all_fields:
            # Should be marked as validatable
            assert FieldValidator.is_field_validatable(field_name), f"{field_name} should be validatable"

            # Should actually work with validate_field
            try:
                # Use a reasonable test value
                if field_name in FieldValidator.INT_FIELDS:
                    test_value = 10
                else:
                    test_value = 0.5

                result = FieldValidator.validate_field(field_name, test_value)
                assert isinstance(result, (int, float))
            except Exception as e:
                pytest.fail(f"validate_field failed for validatable field {field_name}: {e}")

    def test_field_validator_system_field_coverage(self):
        """Integration test: validator covers all expected system fields"""
        # Fields that should be supported based on typical SelfState structure
        expected_system_fields = {
            # Core state fields
            "energy", "integrity", "stability",
            # Event-related fields
            "last_event_intensity",
            # Time-related fields
            "subjective_time", "subjective_time_base_rate",
            "subjective_time_rate_min", "subjective_time_rate_max",
            "subjective_time_intensity_smoothing",
            # Physical/mental state fields
            "fatigue", "tension", "age",
            # System fields
            "ticks", "clarity_duration"
        }

        actual_validatable_fields = set()
        for field in expected_system_fields:
            if FieldValidator.is_field_validatable(field):
                actual_validatable_fields.add(field)

        # All expected fields should be validatable
        missing_fields = expected_system_fields - actual_validatable_fields
        assert len(missing_fields) == 0, f"Missing validatable fields: {missing_fields}"

    def test_field_validator_realistic_value_ranges(self):
        """Integration test: validator handles realistic value ranges"""
        # Test value ranges that might occur in real system operation
        realistic_ranges = {
            "energy": [0.0, 15.0, 50.0, 85.0, 100.0],
            "integrity": [0.0, 0.1, 0.5, 0.9, 1.0],
            "stability": [0.0, 0.2, 0.5, 0.8, 1.0],
            "fatigue": [0.0, 5.0, 25.0, 50.0, 100.0],
            "tension": [0.0, 2.0, 10.0, 20.0, 50.0],
            "ticks": [0, 100, 1000, 10000, 100000],
            "age": [0.0, 10.0, 50.0, 100.0, 500.0],
            "subjective_time": [0.0, 100.0, 1000.0, 10000.0, 100000.0],
        }

        for field_name, test_values in realistic_ranges.items():
            for value in test_values:
                # Should validate without errors for reasonable values
                result = FieldValidator.validate_field(field_name, value)
                assert isinstance(result, (int, float))

                # Should clamp gracefully for extreme values
                clamped = FieldValidator.validate_field(field_name, value, clamp=True)
                assert isinstance(clamped, (int, float))

    def test_field_validator_edge_case_values(self):
        """Integration test: handles edge case values properly"""
        # Test extreme but valid values
        edge_cases = [
            ("energy", 1e-10),          # Very small positive
            ("integrity", 0.999999999), # Very close to 1
            ("fatigue", 1e6),           # Very large value
            ("ticks", 2**31 - 1),       # Large int (close to 32-bit limit)
            ("subjective_time", 1e10),  # Very large float
        ]

        for field_name, value in edge_cases:
            result = FieldValidator.validate_field(field_name, value)
            assert isinstance(result, (int, float))

    def test_field_validator_with_system_imports(self):
        """Integration test: validator works with other system imports"""
        # Test that FieldValidator can be used alongside other system components
        try:
            # Import some related modules to ensure no conflicts
            from src.state.self_state import SelfState
            from src.environment.event import Event

            # Create a mock SelfState-like object
            mock_state = {
                "energy": 75.0,
                "integrity": 0.8,
                "stability": 0.6,
                "fatigue": 15.0,
                "ticks": 1000
            }

            # Validate all fields in the mock state
            for field_name, value in mock_state.items():
                validated = FieldValidator.validate_field(field_name, value)
                assert isinstance(validated, (int, float))

        except ImportError:
            # If related modules can't be imported, skip this test
            pytest.skip("Related system modules not available for integration test")

    def test_field_validator_constants_immutability_integration(self):
        """Integration test: class constants remain consistent across operations"""
        # Store initial state
        initial_bounds = FieldValidator.FIELD_BOUNDS.copy()
        initial_non_neg = FieldValidator.NON_NEGATIVE_FIELDS.copy()
        initial_int = FieldValidator.INT_FIELDS.copy()

        # Perform many operations
        for i in range(100):
            FieldValidator.validate_field("energy", i % 101)
            FieldValidator.validate_field("fatigue", i / 10.0)
            FieldValidator.validate_field("ticks", i)
            FieldValidator.get_field_bounds("energy")
            FieldValidator.is_field_validatable("energy")

        # Constants should remain unchanged
        assert FieldValidator.FIELD_BOUNDS == initial_bounds
        assert FieldValidator.NON_NEGATIVE_FIELDS == initial_non_neg
        assert FieldValidator.INT_FIELDS == initial_int

    def test_field_validator_performance_realistic_load(self):
        """Integration test: validator performs well under realistic load"""
        import time

        # Simulate validating many field updates (like in a running system)
        test_fields = ["energy", "integrity", "stability", "fatigue", "ticks"]
        num_iterations = 1000

        start_time = time.time()

        for i in range(num_iterations):
            for field in test_fields:
                if field == "ticks":
                    value = i
                else:
                    value = (i % 101) / 100.0  # 0.0 to 1.0 range

                result = FieldValidator.validate_field(field, value)
                # Don't clamp to test validation performance
                if field in ["energy", "integrity", "stability"]:
                    result = FieldValidator.validate_field(field, value, clamp=True)

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (less than 1 second for 1000 * 5 operations)
        assert duration < 1.0, f"Validation too slow: {duration:.3f}s for {num_iterations} iterations"

    def test_field_validator_with_json_data_simulation(self):
        """Integration test: validator works with JSON-like data structures"""
        # Simulate loading and validating data from JSON storage
        json_like_data = {
            "energy": 85.0,
            "integrity": 0.92,
            "stability": 0.75,
            "fatigue": 12.5,
            "tension": 8.0,
            "ticks": 1500,
            "age": 45.5,
            "subjective_time": 2341.67,
            "last_event_intensity": 0.4,
            "subjective_time_intensity_smoothing": 0.6,
            "clarity_duration": 30
        }

        # Validate all fields as if loading from persistent storage
        validated_data = {}
        for field_name, value in json_like_data.items():
            validated_data[field_name] = FieldValidator.validate_field(field_name, value)

        # All values should be preserved (since they're all valid)
        for field_name, original_value in json_like_data.items():
            assert validated_data[field_name] == original_value

    def test_field_validator_error_recovery_clamping(self):
        """Integration test: clamping recovers from errors in data streams"""
        # Simulate processing a stream of potentially invalid data
        data_stream = [
            ("energy", 50.0),    # Valid
            ("energy", -10.0),   # Invalid - should clamp
            ("energy", 150.0),   # Invalid - should clamp
            ("integrity", 0.8),  # Valid
            ("integrity", -0.2), # Invalid - should clamp
            ("ticks", 100),      # Valid
            ("ticks", -5),       # Invalid - should clamp
        ]

        # Process stream with clamping enabled (recovery mode)
        results = []
        for field_name, value in data_stream:
            result = FieldValidator.validate_field(field_name, value, clamp=True)
            results.append((field_name, value, result))

        # Verify recovery worked
        expected_results = [
            ("energy", 50.0, 50.0),
            ("energy", -10.0, 0.0),    # Clamped
            ("energy", 150.0, 100.0),  # Clamped
            ("integrity", 0.8, 0.8),
            ("integrity", -0.2, 0.0),  # Clamped
            ("ticks", 100, 100),
            ("ticks", -5, 0),          # Clamped
        ]

        assert results == expected_results