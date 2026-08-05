import uuid
from datetime import datetime


class BaseModel:
    """Base class for all models in the system."""

    def __init__(self):
        self.id = self.generate_id()
        self.created_at = self.get_current_time()
        self.updated_at = self.get_current_time()

    def generate_id(self):
        """Generate a unique ID for the model."""
        return str(uuid.uuid4())

    def get_current_time(self):
        """Get the current time."""
        return datetime.now()

    def save(self):
        """Save the model to the database."""
        self.updated_at = self.get_current_time()

    def update(self, data):
        """Update the model with the given data.

        Applies all attributes atomically: if any value fails validation
        (property setters raise ValueError), previously-applied attributes
        in this same call are rolled back so the object is left unchanged.
        """
        original = {}
        try:
            for key, value in data.items():
                if hasattr(self, key):
                    original[key] = getattr(self, key)
                    setattr(self, key, value)
        except Exception:
            for key, value in original.items():
                setattr(self, key, value)
            raise
        self.save()

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
