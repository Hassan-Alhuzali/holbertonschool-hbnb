import uuid
from datetime import datetime

from app import db


class BaseModel(db.Model):
    """Base class for all models in the system."""

    __abstract__ = True

    id = db.Column(db.String(60), primary_key=True, nullable=False,
                   default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        self.id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        super().__init__(*args, **kwargs)

    def save(self):
        """Save the model to the database."""
        self.updated_at = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

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
