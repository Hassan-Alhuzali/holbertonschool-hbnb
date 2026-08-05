from app.models.base_model import BaseModel


class Amenity(BaseModel):
    """Represents an amenity available for a place."""

    def __init__(self, name):
        """Initialize an Amenity with a name."""
        super().__init__()
        self.name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value or len(value) > 50:
            raise ValueError("Amenity name is required and must be less than 50 characters")
        self._name = value

    def __str__(self):
        return f"Amenity({self.name})"
