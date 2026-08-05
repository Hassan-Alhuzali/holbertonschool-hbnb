import unittest

from app import create_app
from tests.helpers import create_user, create_place, create_amenity


class TestPlaceEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        _, self.owner = create_user(self.client)

    # ---------- POST /api/v1/places/ ----------

    def test_create_place_success(self):
        response, body = create_place(self.client, self.owner["id"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["owner_id"], self.owner["id"])

    def test_create_place_missing_required_field(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "No Price",
            "latitude": 10,
            "longitude": 10,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_empty_title(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "",
            "price": 10,
            "latitude": 10,
            "longitude": 10,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_negative_price(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Negative Price Place",
            "price": -50,
            "latitude": 10,
            "longitude": 10,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_price_zero_is_valid_boundary(self):
        # price is validated as "non-negative", so 0 must be accepted.
        response, _ = create_place(self.client, self.owner["id"], price=0)
        self.assertEqual(response.status_code, 201)

    def test_create_place_latitude_too_high(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Latitude",
            "price": 10,
            "latitude": 90.0001,
            "longitude": 10,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_latitude_too_low(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Latitude",
            "price": 10,
            "latitude": -90.0001,
            "longitude": 10,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_latitude_boundaries_are_valid(self):
        response_low, _ = create_place(self.client, self.owner["id"], latitude=-90)
        response_high, _ = create_place(self.client, self.owner["id"], latitude=90)
        self.assertEqual(response_low.status_code, 201)
        self.assertEqual(response_high.status_code, 201)

    def test_create_place_longitude_too_high(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Longitude",
            "price": 10,
            "latitude": 10,
            "longitude": 180.0001,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_longitude_too_low(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Bad Longitude",
            "price": 10,
            "latitude": 10,
            "longitude": -180.0001,
            "owner_id": self.owner["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_longitude_boundaries_are_valid(self):
        response_low, _ = create_place(self.client, self.owner["id"], longitude=-180)
        response_high, _ = create_place(self.client, self.owner["id"], longitude=180)
        self.assertEqual(response_low.status_code, 201)
        self.assertEqual(response_high.status_code, 201)

    def test_create_place_nonexistent_owner(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Ghost Owner",
            "price": 10,
            "latitude": 10,
            "longitude": 10,
            "owner_id": "does-not-exist",
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_nonexistent_amenity(self):
        response = self.client.post("/api/v1/places/", json={
            "title": "Ghost Amenity",
            "price": 10,
            "latitude": 10,
            "longitude": 10,
            "owner_id": self.owner["id"],
            "amenities": ["does-not-exist"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_place_with_valid_amenity(self):
        _, amenity = create_amenity(self.client)
        response, body = create_place(self.client, self.owner["id"],
                                       amenities=[amenity["id"]])
        self.assertEqual(response.status_code, 201)

    # ---------- GET /api/v1/places/ ----------

    def test_get_all_places(self):
        create_place(self.client, self.owner["id"])
        response = self.client.get("/api/v1/places/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    # ---------- GET /api/v1/places/<id> ----------

    def test_get_place_by_id_includes_owner_and_amenities(self):
        _, amenity = create_amenity(self.client)
        _, created = create_place(self.client, self.owner["id"],
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
        _, created = create_place(self.client, self.owner["id"])
        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "title": "Renamed Place",
            "price": 200.0,
        })
        self.assertEqual(response.status_code, 200)

    def test_update_place_not_found(self):
        response = self.client.put("/api/v1/places/does-not-exist", json={
            "title": "Ghost",
        })
        self.assertEqual(response.status_code, 404)

    def test_update_place_invalid_price(self):
        _, created = create_place(self.client, self.owner["id"])
        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "price": -10,
        })
        self.assertEqual(response.status_code, 400)

    def test_update_place_is_atomic_on_validation_failure(self):
        # Regression test: a failing field in a multi-field PUT must not
        # leave other fields from the same request partially applied.
        #
        # NOTE: Flask's default JSON provider serializes dicts with
        # sort_keys=True, so the test client's `json=` payload always hits
        # the server with keys in alphabetical order, regardless of the
        # order they're written here. We pair 'description' (unvalidated,
        # sorts before 'price') with an invalid 'price' so the unvalidated
        # field is always applied first and 'price' always fails second,
        # deterministically exercising the rollback path either way.
        _, created = create_place(self.client, self.owner["id"],
                                   description="Original description")

        response = self.client.put(f"/api/v1/places/{created['id']}", json={
            "description": "Should Not Stick",
            "price": -999,
        })
        self.assertEqual(response.status_code, 400)

        follow_up = self.client.get(f"/api/v1/places/{created['id']}")
        self.assertEqual(follow_up.get_json()["description"], "Original description")

    # ---------- GET /api/v1/places/<id>/reviews ----------

    def test_get_reviews_for_place_not_found(self):
        response = self.client.get("/api/v1/places/does-not-exist/reviews")
        self.assertEqual(response.status_code, 404)

    def test_get_reviews_for_place_empty_list(self):
        _, created = create_place(self.client, self.owner["id"])
        response = self.client.get(f"/api/v1/places/{created['id']}/reviews")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])


if __name__ == "__main__":
    unittest.main()
