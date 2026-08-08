<<<<<<< HEAD
from app import db
from app.models.base_model import BaseModel
from sqlalchemy.orm import validates
=======
﻿from app import db
from app.models.base_model import BaseModel
from app.models.place import place_amenity

>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe

class Amenity(BaseModel):
    __tablename__ = 'amenities'

<<<<<<< HEAD
    name = db.Column(db.String(128), nullable=False)
=======
    __tablename__ = 'amenities'

    name = db.Column(db.String(50), nullable=False)
    places = db.relationship('Place', secondary=place_amenity,
                             back_populates='amenities', lazy='subquery')

    def __init__(self, name):
        """Initialize an Amenity with a name."""
        super().__init__()
        self.name = name
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe

    @validates('name')
    def validate_name(self, key, value):
        if not value or len(value) > 50:
<<<<<<< HEAD
            raise ValueError("Amenity name is required and must be less than 50 characters")
        return value

=======
            raise ValueError('Amenity name is required and must be less than 50 characters')
        self._name = value

    def __str__(self):
        return f'Amenity({self.name})'
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
