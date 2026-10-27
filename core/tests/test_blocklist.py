import unittest
from blocklist import is_sensitive


class TestSensitiveApps(unittest.TestCase):
    def test_password_manager(self):
        assert is_sensitive("1Password", "") is not None

    def test_bank_app(self):
        assert is_sensitive("Chase", "Accounts overview") is not None

    def test_substring_match(self):
        assert is_sensitive("Bitwarden Password Manager", "") is not None

    def test_case_and_whitespace_insensitive(self):
        assert is_sensitive("  KEYCHAIN ", "") is not None


class TestSensitiveTitles(unittest.TestCase):
    def test_login_page_title(self):
        assert is_sensitive("Google Chrome", "Sign in - Google Accounts") is not None

    def test_incognito(self):
        assert is_sensitive("Safari", "Private Browsing — Start Page") is not None

    def test_credit_card(self):
        assert is_sensitive("Chrome", "Enter your credit card number") is not None

    def test_two_factor(self):
        assert is_sensitive("Chrome", "2FA verification required") is not None

    def test_benign_title(self):
        assert is_sensitive("VSCode", "capture.py - recall_ai") is None

    def test_benign_app_and_title(self):
        assert is_sensitive("", "") is None


if __name__ == "__main__":
    unittest.main()
