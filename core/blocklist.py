PROCESS_NAMES = [
    "1password",
    "bitwarden",
    "keepass",
    "keychain",
    "keychain access",
    "bank of america",
    "chase",
    "wells fargo",
    "capital one",
    "citibank",
    "us bank",
    "mint",
]

WINDOW_KEYWORDS = [
    "incognito",
    "private browsing",
    "private window",
    "passwords",
    "password",
    "bank",
    "sign in",
    "signin",
    "login",
    "payment",
    "credit card",
    "debit card",
    "2fa",
    "two-factor",
]


def is_sensitive(app_name: str, window_title: str) -> str | None:
    app_lower = app_name.lower().strip()
    title_lower = window_title.lower().strip()

    for name in PROCESS_NAMES:
        if name in app_lower:
            return f"sensitive app: {app_name}"

    for kw in WINDOW_KEYWORDS:
        if kw in title_lower:
            return f"sensitive title: \"{kw}\" in \"{window_title}\""

    return None
