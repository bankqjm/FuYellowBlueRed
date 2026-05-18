import re
from typing import Optional


def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 11:
        return phone or ""
    return f"{phone[:3]}****{phone[7:]}"


def mask_amount(amount: float) -> str:
    return f"***.{abs(amount) % 1 * 100:.0f}".replace("0.", ".").ljust(6, "*")[:6]


def mask_id(id_value: Optional[int]) -> str:
    if id_value is None:
        return "***"
    s = str(id_value)
    if len(s) <= 2:
        return "*" * len(s)
    return f"{s[0]}{'*' * (len(s) - 2)}{s[-1]}"


def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"**@{domain}"
    return f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}@{domain}"


def sanitize_log_message(message: str) -> str:
    phone_pattern = r'1[3-9]\d{9}'
    message = re.sub(phone_pattern, lambda m: f"{m.group()[:3]}****{m.group()[7:]}", message)

    id_card_pattern = r'[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx]'
    message = re.sub(id_card_pattern, lambda m: m.group()[:6] + "********" + m.group()[-4:], message)

    return message
