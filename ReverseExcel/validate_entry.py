import re
from datetime import date


# ─────────────────────────────────────────
# INDIVIDUAL FIELD VALIDATORS
# Each returns (is_valid: bool, error_msg: str | None)
# ─────────────────────────────────────────

def validate_date(val) -> tuple:
    if not val:
        return False, "Date is required."
    return True, None


def validate_branch(val: str) -> tuple:
    if not val or val in ("", "— Select —", "— Select Branch first —"):
        return False, "Branch is required."
    return True, None


def validate_area(val: str) -> tuple:
    if not val or val in ("", "— Select —", "— Select Branch first —"):
        return False, "Area is required."
    return True, None


def validate_customer(val: str) -> tuple:
    if not val or val in ("", "— Select —", "— Select Area first —"):
        return False, "Customer is required."
    return True, None


def validate_team_field(val: str, field_name: str) -> tuple:
    """
    Validates Samira Team and Customer Team fields.
    Rules:
    - Required (min 2 chars)
    - Only letters, spaces, commas, full stops allowed
    - No other special characters
    """
    if not val or not val.strip():
        return False, f"{field_name} is required."

    val = val.strip()

    if len(val) < 2:
        return False, f"{field_name} must be at least 2 characters."

    # Allow: letters (including accented), spaces, commas, full stops, hyphens
    if not re.match(r"^[a-zA-Z\s,.\-]+$", val):
        return False, f"{field_name} contains invalid characters. Only letters, spaces, commas, and full stops are allowed."

    return True, None


def validate_samira_team(val: str) -> tuple:
    return validate_team_field(val, "Samira Team")


def validate_customer_team(val: str) -> tuple:
    return validate_team_field(val.strip(), "Customer Team")


def validate_oldest_bill_date(val) -> tuple:
    """Oldest Bill Date cannot be a future date."""
    if not val:
        return False, "Oldest Bill Date is required."
    try:
        # Handle both date objects and strings
        if isinstance(val, str):
            from datetime import datetime
            val = datetime.strptime(val, "%Y-%m-%d").date()
        if val > date.today():
            return False, "Oldest Bill Date cannot be a future date."
        return True, None
    except Exception:
        return False, "Oldest Bill Date is invalid."




def validate_total_outstanding(val) -> tuple:
    if val is None or val == "":
        return False, "Total Outstanding is required."
    try:
        val = float(str(val).replace(",", ""))
        if val < 0:
            return False, "Total Outstanding cannot be negative."
        return True, None
    except Exception:
        return False, "Total Outstanding must be a number."


def validate_follow_up(val: str) -> tuple:
    if not val or val.strip() == "":
        return False, "Follow Up is required."
    if val not in ("Yes", "No"):
        return False, "Follow Up must be Yes or No."
    return True, None


def validate_follow_up_date(val, follow_up: str) -> tuple:
    if follow_up != "Yes":
        return True, None  # only required when follow_up is Yes
    if not val:
        return False, "Follow Up Date is required when Follow Up is Yes."
    try:
        if isinstance(val, str):
            from datetime import datetime
            val = datetime.strptime(val, "%Y-%m-%d").date()
        return True, None
    except Exception:
        return False, "Follow Up Date is invalid."


# ─────────────────────────────────────────
# FULL FORM VALIDATOR
# Call this with all form values at once
# Returns list of error messages (empty = valid)
# ─────────────────────────────────────────

def validate_entry_form(
    visit_date,
    branch: str,
    area: str,
    customer: str,
    samira_team: str,
    customer_team: str,
    oldest_bill_date,
    total_outstanding,
    follow_up: str,
    follow_up_date,
) -> list:
    """
    Runs all validations and returns a list of error strings.
    Empty list means form is valid.
    """
    errors = []

    checks = [
        validate_date(visit_date),
        validate_branch(branch),
        validate_area(area),
        validate_customer(customer),
        validate_samira_team(samira_team),
        validate_customer_team(customer_team),
        validate_oldest_bill_date(oldest_bill_date),
        validate_total_outstanding(total_outstanding),
        validate_follow_up(follow_up),
        validate_follow_up_date(follow_up_date, follow_up),
    ]

    for is_valid, msg in checks:
        if not is_valid and msg:
            errors.append(msg)

    return errors