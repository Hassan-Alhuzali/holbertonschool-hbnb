from app.models.base_model import BaseModel
from app.models.user import User


class Review(BaseModel):
    """Represents a review in the system."""

    def __init__(self, text, rating, place, user):
        """Initialize a new Review instance."""
        super().__init__()
        if place is None or not hasattr(place, "add_review"):
            raise ValueError("place must be a valid Place instance")
        if not isinstance(user, User):
            raise ValueError("user must be a valid User instance")
        self.place = place
        self.user = user
        self.text = text
        self.rating = rating

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if not value:
            raise ValueError("text is required")
        self._text = value

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
            raise ValueError("rating must be an integer between 1 and 5")
        self._rating = value

    def __str__(self):
        """Return a string representation of the review."""
        return f"Review({self.rating}/5: {self.text})"
