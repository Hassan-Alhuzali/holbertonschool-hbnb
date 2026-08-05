import re
from app.models.base_model import BaseModel


class User(BaseModel):
    """Represents a user in the system."""

    def __init__(self, first_name, last_name, email, is_admin=False):
        """Initializes a new User instance."""
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_admin = is_admin

    @property
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        if not value or len(value) > 50:
            raise ValueError("first_name must be provided and less than 50 characters")
        self._first_name = value

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        if not value or len(value) > 50:
            raise ValueError("last_name must be provided and less than 50 characters")
        self._last_name = value

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if not value or not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("Invalid email format")
        self._email = value

    def __str__(self):
        """Returns a string representation of the user."""
        return f"User({self.first_name} {self.last_name}, {self.email})"
