from app import db
from app.models.base_model import BaseModel
from sqlalchemy.orm import validates

class Place(BaseModel):
    __tablename__ = 'places'

    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(1024), nullable=True)
    price = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

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
        return float(value)
