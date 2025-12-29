import re


class Validators:
    @staticmethod
    def is_valid_email(email: str) -> bool:
        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    @staticmethod
    def is_valid_emails(emails: list) -> bool:
        return all(Validators.is_valid_email(email) for email in emails)

    @staticmethod
    def clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()
