<<<<<<< HEAD
from app import db
=======
﻿from app import db
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
from app.models.base_model import BaseModel
from sqlalchemy.orm import validates

place_amenity = db.Table(
    'place_amenity',
    db.Column('place_id', db.String(60), db.ForeignKey('places.id'), primary_key=True),
    db.Column('amenity_id', db.String(60), db.ForeignKey('amenities.id'), primary_key=True)
)


class Place(BaseModel):
    __tablename__ = 'places'

<<<<<<< HEAD
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024), nullable=True)
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
=======
    __tablename__ = 'places'

    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False, default='')
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    owner_id = db.Column(db.String(60), db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('User', back_populates='places', lazy=True)
    reviews = db.relationship('Review', back_populates='place', lazy=True,
                              cascade='all, delete-orphan')
    amenities = db.relationship('Amenity', secondary=place_amenity,
                                back_populates='places', lazy='subquery')

    def __init__(self, title, description, price, latitude, longitude, owner):
        """Initializes a new Place instance."""
        super().__init__()
        if owner is None or not isinstance(owner, User):
            raise ValueError("owner must be a User instance")
        self.owner = owner
        self.title = title
        self.description = '' if description is None else description
        self.price = price
        self.latitude = latitude
        self.longitude = longitude
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe

    @validates('title')
    def validate_title(self, key, value):
        if not value or len(value) > 100:
            raise ValueError("title is required and must be less than 100 characters")
        return value

    @validates('price')
    def validate_price(self, key, value):
        if value is None or float(value) < 0:
            raise ValueError("price must be a non-negative number")
        return float(value)

    @validates('latitude')
    def validate_latitude(self, key, value):
        if value is None or not -90.0 <= float(value) <= 90.0:
            raise ValueError("latitude must be between -90 and 90")
        return float(value)

    @validates('longitude')
    def validate_longitude(self, key, value):
        if value is None or not -180.0 <= float(value) <= 180.0:
            raise ValueError("longitude must be between -180 and 180")
<<<<<<< HEAD
        return float(value)
=======
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
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
