<<<<<<< HEAD
from app import db
=======
﻿from app import db
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
from app.models.base_model import BaseModel
from sqlalchemy.orm import validates

class Review(BaseModel):
    __tablename__ = 'reviews'

<<<<<<< HEAD
    text = db.Column(db.String(1024), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
=======
    __tablename__ = 'reviews'

    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    place_id = db.Column(db.String(60), db.ForeignKey('places.id'), nullable=False)
    user_id = db.Column(db.String(60), db.ForeignKey('users.id'), nullable=False)
    place = db.relationship('Place', back_populates='reviews', lazy=True)
    user = db.relationship('User', back_populates='reviews', lazy=True)

    def __init__(self, text, rating, place, user):
        """Initialize a new Review instance."""
        super().__init__()
        if place is None or not hasattr(place, 'add_review'):
            raise ValueError('place must be a valid Place instance')
        if not isinstance(user, User):
            raise ValueError('user must be a valid User instance')
        self.place = place
        self.user = user
        self.text = text
        self.rating = rating
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe

    @validates('text')
    def validate_text(self, key, value):
        if not value:
<<<<<<< HEAD
            raise ValueError("text is required")
        return value

    @validates('rating')
    def validate_rating(self, key, value):
        if value is None or not (1 <= int(value) <= 5):
            raise ValueError("rating must be between 1 and 5")
        return int(value)
    
=======
            raise ValueError('text is required')
        self._text = value

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 5:
            raise ValueError('rating must be an integer between 1 and 5')
        self._rating = value

    def __str__(self):
        """Return a string representation of the review."""
        return f'Review({self.rating}/5: {self.text})'
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
