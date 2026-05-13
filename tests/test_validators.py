"""Tests for input validation functions in validators.py."""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import validators


class TestIsValidEmail:
    """Test is_valid_email function."""

    def test_valid_emails(self):
        """Test that valid emails are accepted."""
        valid = ['test@example.com', 'user.name@domain.co', 'a@b.c']
        for email in valid:
            assert validators.is_valid_email(email) is True, f"'{email}' should be valid"

    def test_invalid_emails(self):
        """Test that invalid emails are rejected."""
        invalid = ['', 'notanemail', '@domain.com', 'user@', 'user@.com']
        for email in invalid:
            assert validators.is_valid_email(email) is False, f"'{email}' should be invalid"


class TestIsValidPhone:
    """Test is_valid_phone function."""

    def test_valid_phones(self):
        """Test that valid phone numbers are accepted."""
        valid = ['1234567890', '123-456-7890', '+1234567890', '0123456789']
        for phone in valid:
            assert validators.is_valid_phone(phone) is True, f"'{phone}' should be valid"

    def test_invalid_phones(self):
        """Test that invalid phone numbers are rejected."""
        invalid = ['', 'abc', '123', '123456789012345678901']  # 21 chars, too long
        for phone in invalid:
            assert validators.is_valid_phone(phone) is False, f"'{phone}' should be invalid"


class TestIsValidDate:
    """Test is_valid_date function."""

    def test_valid_dates(self):
        """Test that valid dates are accepted."""
        valid = ['2026-05-05', '2024-01-01', '2026-12-31']
        for date in valid:
            assert validators.is_valid_date(date) is True, f"'{date}' should be valid"

    def test_invalid_dates(self):
        """Test that invalid dates are rejected."""
        invalid = ['', '05-05-2026', '2026/05/05', 'notadate', '2026-13-01']
        for date in invalid:
            assert validators.is_valid_date(date) is False, f"'{date}' should be invalid"


class TestIsPositiveNumber:
    """Test is_positive_number function."""

    def test_positive_numbers(self):
        """Test that positive numbers are accepted."""
        valid = ['1', '100', '3.14', '0.5']
        for num in valid:
            assert validators.is_positive_number(num) is True, f"'{num}' should be valid"

    def test_zero_with_allow_zero(self):
        """Test that zero is accepted when allow_zero is True."""
        assert validators.is_positive_number('0', allow_zero=True) is True

    def test_invalid_numbers(self):
        """Test that invalid numbers are rejected."""
        invalid = ['', 'abc', '-1', 'negative', '1.2.3']
        for num in invalid:
            assert validators.is_positive_number(num) is False, f"'{num}' should be invalid"


class TestValidateEmployeeData:
    """Test validate_employee_data function."""

    def test_valid_data(self):
        """Test that valid employee data passes."""
        is_valid, msg = validators.validate_employee_data(
            name='John Doe',
            department='IT',
            position='Developer',
            salary='5000',
            email='john@example.com',
            phone='1234567890'
        )
        assert is_valid is True
        assert msg == ''

    def test_missing_name(self):
        """Test that missing name fails."""
        is_valid, msg = validators.validate_employee_data(
            name='',
            department='IT',
            position='Developer',
            salary='5000',
            email='john@example.com',
            phone='1234567890'
        )
        assert is_valid is False
        assert 'اسم' in msg or 'name' in msg.lower()

    def test_invalid_email(self):
        """Test that invalid email fails."""
        is_valid, msg = validators.validate_employee_data(
            name='John Doe',
            department='IT',
            position='Developer',
            salary='5000',
            email='invalid',
            phone='1234567890'
        )
        assert is_valid is False

    def test_invalid_phone(self):
        """Test that invalid phone fails."""
        is_valid, msg = validators.validate_employee_data(
            name='John Doe',
            department='IT',
            position='Developer',
            salary='5000',
            email='john@example.com',
            phone='abc'
        )
        assert is_valid is False

    def test_invalid_salary(self):
        """Test that invalid salary fails."""
        is_valid, msg = validators.validate_employee_data(
            name='John Doe',
            department='IT',
            position='Developer',
            salary='invalid',
            email='john@example.com',
            phone='1234567890'
        )
        assert is_valid is False


class TestValidateLeaveDates:
    """Test validate_leave_dates function."""

    def test_valid_dates(self):
        """Test that valid date range passes."""
        is_valid, msg = validators.validate_leave_dates('2026-05-05', '2026-05-10')
        assert is_valid is True

    def test_end_before_start(self):
        """Test that end date before start date fails."""
        is_valid, msg = validators.validate_leave_dates('2026-05-10', '2026-05-05')
        assert is_valid is False

    def test_invalid_date_format(self):
        """Test that invalid date format fails."""
        is_valid, msg = validators.validate_leave_dates('05-05-2026', '2026-05-10')
        assert is_valid is False

    def test_same_date(self):
        """Test that same start and end date is valid."""
        is_valid, msg = validators.validate_leave_dates('2026-05-05', '2026-05-05')
        assert is_valid is True
