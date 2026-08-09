from app import db
from app.models.base_model import BaseModel
from sqlalchemy.orm import validates

class Review(BaseModel):
    __tablename__ = 'reviews'

    text = db.Column(db.String(1024), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    @validates('text')
    def validate_text(self, key, value):
        if not value:
            raise ValueError("text is required")
        return value

    @validates('rating')
    def validate_rating(self, key, value):
        if value is None or not (1 <= int(value) <= 5):
            raise ValueError("rating must be between 1 and 5")
        return int(value)
    
