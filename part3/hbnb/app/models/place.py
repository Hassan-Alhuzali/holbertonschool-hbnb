from app.models.base_model import BaseModel
from app.models.user import User

class Place(BaseModel):
    """Represents a place in the system."""

    def __init__(self, title, description, price, latitude, longitude, owner):
        """Initializes a new Place instance."""
        super().__init__()
        if owner is None or not isinstance(owner, User):
            raise ValueError("owner must be a User instance")
        self.owner = owner
        self.title = title
        self.description = description
        self.price = price
        self.latitude = latitude
        self.longitude = longitude
        self.reviews = []
        self.amenities = []

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        if not value or len(value) > 100:
            raise ValueError("title is required and must be less than 100 characters")
        self._title = value

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value is None or float(value) < 0:
            raise ValueError("price must be a non-negative number")
        self._price = float(value)

    @property
    def latitude(self):
        return self._latitude

    @latitude.setter
    def latitude(self, value):
        if value is None or not -90.0 <= float(value) <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        self._latitude = float(value)

    @property
    def longitude(self):
        return self._longitude

    @longitude.setter
    def longitude(self, value):
        if value is None or not -180.0 <= float(value) <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
        self._longitude = float(value)

    def add_review(self, review):
        """Add a review to the place."""
        self.reviews.append(review)

    def add_amenity(self, amenity):
        """Add an amenity to the place."""
        self.amenities.append(amenity)

    def __str__(self):
        """Return a string representation of the place."""
        return f"Place({self.title}, {self.price})"
