<<<<<<< HEAD
from app import db, bcrypt
=======
﻿import re

from app import db
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
from app.models.base_model import BaseModel
import re
from sqlalchemy.orm import validates

class User(BaseModel):
    __tablename__ = 'users'

<<<<<<< HEAD
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
=======
    __tablename__ = 'users'

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    places = db.relationship('Place', back_populates='owner', lazy=True,
                             cascade='all, delete-orphan')
    reviews = db.relationship('Review', back_populates='user', lazy=True,
                              cascade='all, delete-orphan')

    def __init__(self, first_name, last_name, email, is_admin=False):
        """Initializes a new User instance."""
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.is_admin = is_admin
        self.password = None  # stores the hashed password
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe

    @validates('email')
    def validate_email(self, key, value):
        """Validate email format before saving to database."""
        if not value or not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("Invalid email format")
        return value
    
    
    def hash_password(self, password):
        """Hash the password before storing it."""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        """Verify the hashed password."""
        return bcrypt.check_password_hash(self.password, password)

<<<<<<< HEAD
    def to_dict(self):
        """Convert the User model instance to a dictionary."""
        user_dict = super().to_dict()
        
        user_dict.update({
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'is_admin': self.is_admin
        })
        return user_dict
=======
    def __str__(self):
        """Returns a string representation of the user."""
        return f"User({self.first_name} {self.last_name}, {self.email})"
>>>>>>> a0cb86aa3f9ff58668ee8f970e679dd650ac27fe
