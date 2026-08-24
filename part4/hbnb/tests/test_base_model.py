import unittest

from app.models.user import User
from app.models.place import Place
from app.models.amenity import Amenity


class TestBaseModelUpdateAtomicity(unittest.TestCase):
    """Direct, order-controlled tests for BaseModel.update().

    These bypass HTTP/JSON entirely (plain Python dicts preserve exactly
    the key order written in source) so the rollback behavior is pinned
    down precisely, rather than depending on how any particular transport
    happens to order request keys.
    """

    def test_update_rolls_back_earlier_fields_when_a_later_one_is_invalid(self):
        owner = User("Owner", "Person", "atomic.owner@example.com")
        place = Place("Original Title", "Original description", 50, 5, 5, owner)

        with self.assertRaises(ValueError):
            place.update({"title": "Mutated Title", "price": -999})

        self.assertEqual(place.title, "Original Title")
        self.assertEqual(place.price, 50)

    def test_update_rolls_back_regardless_of_which_field_is_invalid_first(self):
        # Same as above, but with the invalid field listed first, to prove
        # the rollback doesn't depend on which key happens to be processed
        # first.
        owner = User("Owner", "Person", "atomic.owner2@example.com")
        place = Place("Original Title", "Original description", 50, 5, 5, owner)

        with self.assertRaises(ValueError):
            place.update({"price": -999, "title": "Mutated Title"})

        self.assertEqual(place.title, "Original Title")
        self.assertEqual(place.price, 50)

    def test_update_applies_all_fields_when_all_are_valid(self):
        owner = User("Owner", "Person", "atomic.owner3@example.com")
        place = Place("Original Title", "Original description", 50, 5, 5, owner)

        place.update({"title": "New Title", "price": 75})

        self.assertEqual(place.title, "New Title")
        self.assertEqual(place.price, 75)

    def test_user_update_rolls_back_on_invalid_email(self):
        user = User("Original", "Name", "atomic.user@example.com")

        with self.assertRaises(ValueError):
            user.update({"first_name": "Mutated", "email": "not-an-email"})

        self.assertEqual(user.first_name, "Original")
        self.assertEqual(user.email, "atomic.user@example.com")

    def test_amenity_update_rolls_back_on_invalid_name(self):
        amenity = Amenity("Original Name")

        with self.assertRaises(ValueError):
            amenity.update({"name": ""})

        self.assertEqual(amenity.name, "Original Name")


if __name__ == "__main__":
    unittest.main()
