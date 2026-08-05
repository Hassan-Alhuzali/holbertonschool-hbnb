import unittest

from app import create_app
from tests.helpers import (
    create_admin_and_login,
    create_user_and_login,
    create_amenity,
    create_place,
)


class TestPlaceEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Admin needed to create amenities.
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        # Regular user who will own places.
        self.owner, self.owner_token = create_user_and_login(self.client, self.app)

    # ---------- POST /api/v1/places/ ----------

    def test_create_place_success(self):
        response, body = create_place(self.client, self.owner_token)
        self.assertEqual(response.status_code, 201)
        # The owner_id in the response must match the authenticated user.
        self.assertEqual(body["owner_id"], self.owner["id"])

    def test_create_place_without_token_returns_401(self):
        """POST /api/v1/places/ must require a JWT token."""
        response = self.client.post("/api/v1/places/", json={
            "title": "No Auth Place",
            "price": 50.0,
            "latitude": 10.0,
            "longitude": 10.0,
        })
        self.assertEqual(response.status_code, 401)

    def test_create_place_missing_required_field(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "No Price",
            "latitude": 10,
            "longitude": 10,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_empty_title(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "",
            "price": 10,
            "latitude": 10,
            "longitude": 10,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_negative_price(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Negative Price Place",
            "price": -50,
            "latitude": 10,
            "longitude": 10,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_price_zero_is_valid_boundary(self):
        # price is validated as "non-negative", so 0 must be accepted.
        response, _ = create_place(self.client, self.owner_token, price=0)
        self.assertEqual(response.status_code, 201)

    def test_create_place_latitude_too_high(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Latitude",
            "price": 10,
            "latitude": 90.0001,
            "longitude": 10,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_latitude_too_low(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Latitude",
            "price": 10,
            "latitude": -90.0001,
            "longitude": 10,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_latitude_boundaries_are_valid(self):
        response_low, _ = create_place(self.client, self.owner_token, latitude=-90)
        response_high, _ = create_place(self.client, self.owner_token, latitude=90)
        self.assertEqual(response_low.status_code, 201)
        self.assertEqual(response_high.status_code, 201)

    def test_create_place_longitude_too_high(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Longitude",
            "price": 10,
            "latitude": 10,
            "longitude": 180.0001,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_longitude_too_low(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Longitude",
            "price": 10,
            "latitude": 10,
            "longitude": -180.0001,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_longitude_boundaries_are_valid(self):
        response_low, _ = create_place(self.client, self.owner_token, longitude=-180)
        response_high, _ = create_place(self.client, self.owner_token, longitude=180)
        self.assertEqual(response_low.status_code, 201)
        self.assertEqual(response_high.status_code, 201)

    def test_create_place_nonexistent_amenity(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Ghost Amenity",
            "price": 10,
            "latitude": 10,
            "longitude": 10,
            "amenities": ["does-not-exist"],
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_place_with_valid_amenity(self):
        _, amenity = create_amenity(self.client, self.admin_token)
        response, body = create_place(self.client, self.owner_token,
                                       amenities=[amenity["id"]])
        self.assertEqual(response.status_code, 201)

    # ---------- GET /api/v1/places/ (public) ----------

    def test_get_all_places(self):
        create_place(self.client, self.owner_token)
        response = self.client.get("/api/v1/places/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    # ---------- GET /api/v1/places/<id> (public) ----------

    def test_get_place_by_id_includes_owner_and_amenities(self):
        _, amenity = create_amenity(self.client, self.admin_token)
        _, created = create_place(self.client, self.owner_token,
                                   amenities=[amenity["id"]])
        response = self.client.get(f"/api/v1/places/{created['id']}")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["owner"]["id"], self.owner["id"])
        self.assertEqual(len(body["amenities"]), 1)
        self.assertEqual(body["amenities"][0]["id"], amenity["id"])

    def test_get_place_not_found(self):
        response = self.client.get("/api/v1/places/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/places/<id> ----------

    def test_update_place_success(self):
        _, created = create_place(self.client, self.owner_token)
        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "title": "Renamed Place",
            "price": 200.0,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 200)

    def test_update_place_without_token_returns_401(self):
        """PUT /api/v1/places/<id> must require a JWT token."""
        _, created = create_place(self.client, self.owner_token)
        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "title": "No Auth",
        })
        self.assertEqual(response.status_code, 401)

    def test_update_place_not_found(self):
        response = self.client.put("/api/v1/places/does-not-exist", json={
            "title": "Ghost",
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 404)

    def test_update_place_invalid_price(self):
        _, created = create_place(self.client, self.owner_token)
        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "price": -10,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

    def test_update_place_is_atomic_on_validation_failure(self):
        # Regression test: a failing field in a multi-field PUT must not
        # leave other fields from the same request partially applied.
        _, created = create_place(self.client, self.owner_token,
                                   description="Original description")

        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "description": "Should Not Stick",
            "price": -999,
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)

        follow_up = self.client.get(f"/api/v1/places/{created['id']}")
        self.assertEqual(follow_up.get_json()["description"], "Original description")

    # ---------- GET /api/v1/places/<id>/reviews ----------

    def test_get_reviews_for_place_not_found(self):
        response = self.client.get("/api/v1/places/does-not-exist/reviews")
        self.assertEqual(response.status_code, 404)

    def test_get_reviews_for_place_empty_list(self):
        _, created = create_place(self.client, self.owner_token)
        response = self.client.get(f"/api/v1/places/{created['id']}/reviews")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])


if __name__ == "__main__":
    unittest.main()
