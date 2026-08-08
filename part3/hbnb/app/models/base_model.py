import uuid
from datetime import datetime
from app import db

<<<<<<< HEAD
class BaseModel(db.Model):
    __abstract__ = True  # This ensures SQLAlchemy does not create a table for BaseModel

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

=======
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
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe

    def update(self, data):
        """Update the model with the given data."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
                
def to_dict(self):
        """Convert the SQLAlchemy model instance to a dictionary."""
        return {
<<<<<<< HEAD
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
=======
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
