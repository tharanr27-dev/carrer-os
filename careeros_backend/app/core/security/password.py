import re


class PasswordPolicyException(Exception):
    pass


class PasswordValidator:
    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_number: bool = True,
        require_special: bool = True,
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_number = require_number
        self.require_special = require_special

    def validate(self, password: str) -> None:
        if len(password) < self.min_length:
            raise PasswordPolicyException(
                f"Password must be at least {self.min_length} characters long."
            )

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            raise PasswordPolicyException("Password must contain at least one uppercase letter.")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            raise PasswordPolicyException("Password must contain at least one lowercase letter.")

        if self.require_number and not re.search(r"\d", password):
            raise PasswordPolicyException("Password must contain at least one number.")

        if self.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise PasswordPolicyException("Password must contain at least one special character.")


password_validator = PasswordValidator()
