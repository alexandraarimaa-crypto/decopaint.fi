"""Normalize web identifiers before using them in GA4 Measurement Protocol.

Cookie envelopes are not client/session identifiers. Accept known web cookie
formats and canonical values; never invent an identity for a consented user.
"""

import re

CLIENT = re.compile(r"[0-9]{1,20}\.[0-9]{1,20}\Z")
SESSION = re.compile(r"[0-9]{1,20}\Z")


def parse_ga_client_id(value):
    if not isinstance(value, str) or len(value) > 512:
        return ""
    value = value.strip()
    wrapped = re.fullmatch(r"GA[0-9]+\.[0-9]+\.([0-9]+\.[0-9]+)", value)
    if wrapped:
        value = wrapped.group(1)
    return value if CLIENT.fullmatch(value) else ""


def parse_ga_session_id(value):
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        return ""
    value = str(value).strip()
    if len(value) > 512:
        return ""
    if value.startswith("GS1."):
        parts = value.split(".")
        value = parts[2] if len(parts) >= 4 else ""
    elif value.startswith("GS2."):
        parts = value.split(".", 2)
        match = re.search(r"(?:^|\$)s([0-9]+)(?:\$|$)", parts[2] if len(parts) == 3 else "")
        value = match.group(1) if match else ""
    if not SESSION.fullmatch(value) or int(value) <= 0:
        return ""
    return str(int(value))
