"""Input validation utilities for the HR system."""
import re
from datetime import datetime


def is_valid_email(email: str) -> bool:
    """Check if email format is valid."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{1,}$'
    return re.match(pattern, email) is not None


def is_valid_phone(phone: str) -> bool:
    """Check if phone number is valid (allows digits, spaces, dashes, plus)."""
    if not phone:
        return False
    pattern = r'^[\d\s\-+]{7,20}$'
    return re.match(pattern, phone) is not None


def is_valid_date(date_str: str, fmt: str = '%Y-%m-%d') -> bool:
    """Check if date string is valid for given format."""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, fmt)
        return True
    except ValueError:
        return False


def is_positive_number(value, allow_zero: bool = False) -> bool:
    """Check if value is a positive number."""
    try:
        num = float(value)
        return num > 0 or (allow_zero and num >= 0)
    except (ValueError, TypeError):
        return False


def is_non_empty_string(value: str, min_len: int = 1) -> bool:
    """Check if string is non-empty (after stripping)."""
    return bool(value and value.strip() and len(value.strip()) >= min_len)


def validate_employee_data(name, department, position, salary, email='', phone='') -> tuple:
    """Validate employee form data. Returns (is_valid, error_message)."""
    if not is_non_empty_string(name):
        return False, "اسم الموظف مطلوب."
    if not is_non_empty_string(department):
        return False, "القسم مطلوب."
    if not is_non_empty_string(position):
        return False, "الوظيفة مطلوبة."
    if not is_positive_number(salary, allow_zero=True):
        return False, "الراتب يجب أن يكون رقماً صحيحاً (صفر أو أكبر)."
    if email and not is_valid_email(email):
        return False, "صيغة البريد الإلكتروني غير صحيحة."
    if phone and not is_valid_phone(phone):
        return False, "صيغة رقم الهاتف غير صحيحة."
    return True, ""


def validate_leave_dates(start_date, end_date) -> tuple:
    """Validate leave request dates."""
    if not is_valid_date(start_date):
        return False, "تاريخ البداية غير صحيح."
    if not is_valid_date(end_date):
        return False, "تاريخ النهاية غير صحيح."
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if end < start:
            return False, "تاريخ النهاية يجب أن يكون بعد تاريخ البداية."
    except ValueError:
        return False, "صيغة التاريخ غير صحيحة."
    return True, ""
