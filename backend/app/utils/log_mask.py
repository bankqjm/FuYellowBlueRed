"""Sensitive data masking utilities for log output.

These functions mask sensitive information (phone numbers, amounts,
ID cards, bank cards, emails) in log messages to prevent privacy leaks.
They only affect log output — database and API responses remain unchanged.
"""

import re


def mask_phone(phone: str) -> str:
    """Mask phone number: keep first 3 and last 4 digits, replace middle with ****.

    Example: 13812345678 -> 138****5678
    """
    if not phone or len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def mask_amount(amount) -> str:
    """Mask monetary amount: keep integer part, replace decimal with **.

    Example: 128.50 -> 128.** ; 1000.00 -> 1000.**
    """
    try:
        str_amount = str(amount)
        if "." in str_amount:
            integer_part = str_amount.split(".")[0]
            return f"{integer_part}.**"
        return f"{str_amount}.**"
    except Exception:
        return "***.**"


def mask_id_card(id_card: str) -> str:
    """Mask ID card number: keep first 3 and last 4 digits, middle with ********.

    Example: 110101199001011234 -> 110***************234
    """
    if not id_card or len(id_card) < 8:
        return id_card
    return f"{id_card[:3]}{'*' * (len(id_card) - 7)}{id_card[-4:]}"


def mask_bank_card(card_no: str) -> str:
    """Mask bank card number: keep only last 4 digits, rest with ****.

    Example: 6222021234561234 -> ****1234
    """
    if not card_no or len(card_no) < 5:
        return card_no
    return f"****{card_no[-4:]}"


def mask_email(email: str) -> str:
    """Mask email: keep first and last character before @, rest with ***.

    Example: testuser@example.com -> t***r@example.com
    """
    if not email or "@" not in email:
        return email
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = f"{local[0]}***"
    else:
        masked_local = f"{local[0]}***{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_phone_in_text(text: str) -> str:
    """Find and mask all phone numbers in a text string.

    Matches Chinese mobile numbers (1[3-9]XXXXXXXXX).
    """
    if not text:
        return text
    return re.sub(r"(1[3-9]\d)\d{4}(\d{4})", r"\1****\2", text)
