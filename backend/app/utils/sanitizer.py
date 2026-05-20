"""Input sanitization utilities for XSS prevention.

Provides functions to strip or sanitize HTML from user input:
- strip_all_tags: Remove all HTML tags (for plain text fields)
- sanitize_limited_html: Allow only safe basic tags (for formatted fields)
- strip_dangerous_content: Remove script/iframe/event handlers (for semi-rich fields)
"""

import bleach

# Tags allowed in "limited formatting" fields (description, notice)
ALLOWED_TAGS = ["p", "br", "b", "i", "strong", "em", "ul", "ol", "li"]

# Attributes allowed on any tag (none by default — no style/class/id)
ALLOWED_ATTRIBUTES: dict = {}

# Protocols that are considered dangerous
DENIED_PROTOCOLS = {"javascript", "vbscript", "data"}


def strip_all_tags(text: str) -> str:
    """Remove all HTML tags and return plain text.

    Use for: review content, order remark, nickname, phone, address.
    Also strips javascript: protocol references.
    """
    if not text:
        return text
    cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)
    return cleaned.strip()


def sanitize_limited_html(text: str) -> str:
    """Allow a small set of safe formatting tags, strip everything else.

    Use for: product description, shop notice.
    Allows: <p>, <br>, <b>, <i>, <strong>, <em>, <ul>, <ol>, <li>
    """
    if not text:
        return text
    cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return cleaned.strip()


def strip_dangerous_content(text: str) -> str:
    """Strip <script>, <iframe>, and on* event attributes but keep basic inline formatting.

    Use for: shop name, product name (shouldn't have any HTML but be safe).
    This is a middle ground: allow safe text through but block XSS vectors.
    """
    if not text:
        return text
    # Remove dangerous tags and attributes
    dangerous_tags = ["script", "iframe", "object", "embed", "form", "input", "textarea"]
    cleaned = bleach.clean(
        text,
        tags=[tag for tag in bleach.ALLOWED_TAGS if tag not in dangerous_tags],
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return cleaned.strip()
