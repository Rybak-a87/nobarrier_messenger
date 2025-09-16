import re
from dataclasses import dataclass


class WeakPasswordError(Exception):
    pass


@dataclass
class UserEntity:
    username: str
    password: str

    def validate_password(self) -> None:
        checks = {
            "uppercase letter": r"[A-Z]",
            "lowercase letter": r"[a-z]",
            "digit": r"\d",
            "special character": r"[!@#$%^&*(),.?\":{}|<>]"
        }
        for error_name, pattern in checks.items():
            if not re.search(pattern, self.password):
                raise WeakPasswordError(f"Password must contain at least one {error_name}")
