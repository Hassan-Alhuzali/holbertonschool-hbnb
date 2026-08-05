from app.persistence.repository import InMemoryRepository
from app.models.amenity import Amenity
from app.models.user import User
from app.models.place import Place
from app.models.review import Review


class HBnBFacade:
    def __init__(self):
        self.user_repo = InMemoryRepository()
        self.place_repo = InMemoryRepository()
        self.review_repo = InMemoryRepository()
        self.amenity_repo = InMemoryRepository()

    # ---------- Amenity ----------
    def create_amenity(self, amenity_data):
        amenity = Amenity(**amenity_data)
        self.amenity_repo.add(amenity)
        return amenity

    def get_amenity(self, amenity_id):
        return self.amenity_repo.get(amenity_id)

    def get_all_amenities(self):
        return self.amenity_repo.get_all()

    def update_amenity(self, amenity_id, amenity_data):
        amenity = self.amenity_repo.get(amenity_id)
        if not amenity:
            return None
        allowed = {k: v for k, v in amenity_data.items()
                   if k in ['name']}
        self.amenity_repo.update(amenity_id, allowed)
        return amenity

    # ---------- User (needed for Place owner) ----------
    def create_user(self, user_data):
        user = User(**user_data)
        self.user_repo.add(user)
        return user

    def get_user(self, user_id):
        return self.user_repo.get(user_id)

    def get_all_users(self):
        return self.user_repo.get_all()

    def get_user_by_email(self, email):
        return self.user_repo.get_by_attribute('email', email)

    def update_user(self, user_id, user_data):
        user = self.user_repo.get(user_id)
        if not user:
            return None
        allowed = {k: v for k, v in user_data.items()
                   if k in ['first_name', 'last_name', 'email']}
        self.user_repo.update(user_id, allowed)
        return user

    # ---------- Place ----------
    def create_place(self, place_data):
        owner_id = place_data.get('owner_id')
        owner = self.user_repo.get(owner_id)
        if not owner:
            raise ValueError("Owner not found")

        amenities_ids = place_data.get('amenities', [])
        amenity_objs = []
        for aid in amenities_ids:
            amenity = self.amenity_repo.get(aid)
            if not amenity:
                raise ValueError(f"Amenity {aid} not found")
            amenity_objs.append(amenity)

        place = Place(
            title=place_data['title'],
            description=place_data.get('description', ''),
            price=place_data['price'],
            latitude=place_data['latitude'],
            longitude=place_data['longitude'],
            owner=owner
        )
        for amenity in amenity_objs:
            place.add_amenity(amenity)

        self.place_repo.add(place)
        return place

    def get_place(self, place_id):
        return self.place_repo.get(place_id)

    def get_all_places(self):
        return self.place_repo.get_all()

    def update_place(self, place_id, place_data):
        place = self.place_repo.get(place_id)
        if not place:
            return None
        allowed = {k: v for k, v in place_data.items()
                   if k in ['title', 'description', 'price', 'latitude', 'longitude']}
        self.place_repo.update(place_id, allowed)
        return place

    # ---------- Review ----------
    def create_review(self, review_data):
        place = self.place_repo.get(review_data.get('place_id'))
        if not place:
            raise ValueError("Place not found")

        user = self.user_repo.get(review_data.get('user_id'))
        if not user:
            raise ValueError("User not found")

        review = Review(
            text=review_data.get('text'),
            rating=review_data.get('rating'),
            place=place,
            user=user
        )
        self.review_repo.add(review)
        place.add_review(review)
        return review

    def get_review(self, review_id):
        return self.review_repo.get(review_id)

    def get_all_reviews(self):
        return self.review_repo.get_all()

    def get_reviews_by_place(self, place_id):
        place = self.place_repo.get(place_id)
        if place is None:
            return None
        return place.reviews

    def update_review(self, review_id, review_data):
        review = self.review_repo.get(review_id)
        if not review:
            return None
        allowed = {k: v for k, v in review_data.items()
                   if k in ['text', 'rating']}
        self.review_repo.update(review_id, allowed)
        return review

    def delete_review(self, review_id):
        review = self.review_repo.get(review_id)
        if not review:
            return None
        if review in review.place.reviews:
            review.place.reviews.remove(review)
        self.review_repo.delete(review_id)
        return review
