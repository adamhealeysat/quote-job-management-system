"""
ui/validators.py - Quote & Job Management System

Centralised input validation for the Quote & Job Management System.
Every rule here comes directly from the Data Dictionary (Criterion 5,
section 2.1) so that customers.py, quotes.py, jobs.py, settings.py and
auth.py all enforce the same constraints instead of each screen having
its own (looser) checks.

@author ***Adam Healey***
"""

import re
from datetime import date

CURRENT_YEAR = date.today().year

NAME_PATTERN = re.compile(r"^[A-Za-z ]+$")
PHONE_PATTERN = re.compile(r"^\d{10}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
REGO_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


# ----------------------------------------------------------------------
# Customer fields
# ----------------------------------------------------------------------

def validate_customer_name(name: str):
    name = (name or "").strip()
    if not name:
        return False, "Customer name is required"
    if len(name) > 100:
        return False, "Customer name must be 100 characters or fewer"
    if not NAME_PATTERN.match(name):
        return False, "Customer name must contain letters and spaces only"
    return True, ""


def validate_phone(phone: str):
    phone = (phone or "").strip()
    if not phone:
        return False, "Phone number is required"
    if not PHONE_PATTERN.match(phone):
        return False, "Phone number must be exactly 10 digits"
    return True, ""


def validate_email(email: str):
    email = (email or "").strip()
    if not email:
        return True, ""  # optional field
    if not EMAIL_PATTERN.match(email):
        return False, "Email must contain @ and a domain (e.g. name@example.com)"
    return True, ""


def validate_vehicle_make(make: str):
    make = (make or "").strip()
    if not make:
        return False, "Vehicle make is required"
    if len(make) > 50:
        return False, "Vehicle make must be 50 characters or fewer"
    return True, ""


def validate_vehicle_model(model: str):
    model = (model or "").strip()
    if not model:
        return False, "Vehicle model is required"
    if len(model) > 50:
        return False, "Vehicle model must be 50 characters or fewer"
    return True, ""


def validate_vehicle_year(year_str: str):
    year_str = (year_str or "").strip()
    if not year_str:
        return False, "Vehicle year is required"
    if not year_str.isdigit() or len(year_str) != 4:
        return False, "Vehicle year must be a 4-digit number"
    year = int(year_str)
    if year < 1900 or year > CURRENT_YEAR:
        return False, f"Vehicle year must be between 1900 and {CURRENT_YEAR}"
    return True, ""


def validate_vehicle_rego(rego: str):
    rego = (rego or "").strip()
    if not rego:
        return False, "Vehicle rego is required"
    if len(rego) > 10:
        return False, "Rego must be 10 characters or fewer"
    if not REGO_PATTERN.match(rego):
        return False, "Rego must contain letters or numbers only"
    return True, ""


def validate_customer_fields(name, phone, email, make, model, year_str, rego):
    """
    Run every Customer field check in Data Dictionary order and return
    (is_valid, error_message) for the FIRST failing field. Used by both
    customers.py and the "add customer" dialog embedded in quotes.py so
    the two forms can never drift apart.
    """
    checks = [
        validate_customer_name(name),
        validate_phone(phone),
        validate_email(email),
        validate_vehicle_make(make),
        validate_vehicle_model(model),
        validate_vehicle_year(year_str),
        validate_vehicle_rego(rego),
    ]
    for is_valid, message in checks:
        if not is_valid:
            return False, message
    return True, ""


# ----------------------------------------------------------------------
# Quote / QuoteLineItem fields
# ----------------------------------------------------------------------

def validate_notes(notes: str, max_length: int = 500):
    notes = (notes or "").strip()
    if not notes:
        return True, ""  # optional field
    if len(notes) > max_length:
        return False, f"Notes must be {max_length} characters or fewer"
    return True, ""


def validate_line_description(description: str):
    description = (description or "").strip()
    if not description:
        return False, "Line item description is required"
    if len(description) > 200:
        return False, "Line item description must be 200 characters or fewer"
    return True, ""


def validate_quantity(quantity_str: str):
    quantity_str = (quantity_str or "").strip()
    if not quantity_str:
        return False, "Quantity is required"
    try:
        quantity = float(quantity_str)
    except ValueError:
        return False, "Quantity must be a number"
    if quantity <= 0:
        return False, "Quantity must be greater than 0"
    # max 2 decimal places
    if round(quantity, 2) != quantity:
        return False, "Quantity must have at most 2 decimal places"
    return True, ""


def validate_unit_price(price_str: str):
    price_str = (price_str or "").strip()
    if not price_str:
        return False, "Unit price is required"
    try:
        price = float(price_str)
    except ValueError:
        return False, "Unit price must be a number"
    if price < 0:
        return False, "Unit price must be 0 or greater"
    return True, ""


def validate_line_item(description, quantity_str, unit_price_str):
    """
    Validate one quote line item and, on success, return the parsed
    numeric values so callers don't have to re-parse them.

    Returns (is_valid, error_message, parsed) where parsed is either
    None (on failure) or a dict with float 'quantity' and 'unit_price'.
    """
    for is_valid, message in (
        validate_line_description(description),
        validate_quantity(quantity_str),
        validate_unit_price(unit_price_str),
    ):
        if not is_valid:
            return False, message, None

    return True, "", {
        "quantity": float(quantity_str.strip()),
        "unit_price": float(unit_price_str.strip()),
    }


# ----------------------------------------------------------------------
# Job fields
# ----------------------------------------------------------------------

def validate_job_notes(notes: str):
    return validate_notes(notes, max_length=500)


# ----------------------------------------------------------------------
# User / auth fields
# ----------------------------------------------------------------------

def validate_username(username: str):
    username = (username or "").strip()
    if not username:
        return False, "Username is required"
    if len(username) > 50:
        return False, "Username must be 50 characters or fewer"
    return True, ""


def validate_password(password: str, min_length: int = 4):
    """
    The Data Dictionary only specifies that passwords are hashed, not a
    minimum length. settings.py already enforced a 4-character minimum
    for password resets, so that convention is kept here and reused for
    new-user creation too, for consistency between the two forms.
    """
    if not password:
        return False, "Password is required"
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    return True, ""


# ----------------------------------------------------------------------
# Parts catalogue / labour rate (Settings screen; not in the original
# Data Dictionary but included here so all numeric-money input in the
# app is validated the same way)
# ----------------------------------------------------------------------

def validate_part_name(name: str):
    name = (name or "").strip()
    if not name:
        return False, "Part name is required"
    if len(name) > 100:
        return False, "Part name must be 100 characters or fewer"
    return True, ""


def validate_currency_amount(amount_str: str, field_label: str = "Amount"):
    amount_str = (amount_str or "").strip()
    if not amount_str:
        return False, f"{field_label} is required"
    try:
        amount = float(amount_str)
    except ValueError:
        return False, f"{field_label} must be a number"
    if amount < 0:
        return False, f"{field_label} must be 0 or greater"
    return True, ""