import unittest

from app import create_app
from tests.helpers import create_amenity, unique_suffix


class TestAmenityEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    # ---------- POST /api/v1/amenities/ ----------

    def test_create_amenity_success(self):
        response, body = create_amenity(self.client, "Wi-Fi-" + unique_suffix())
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", body)
        self.assertIn("name", body)

    def test_create_amenity_empty_name(self):
        response = self.client.post("/api/v1/amenities/", json={"name": ""})
        self.assertEqual(response.status_code, 400)

    def test_create_amenity_missing_field(self):
        response = self.client.post("/api/v1/amenities/", json={})
        self.assertEqual(response.status_code, 400)

    def test_create_amenity_name_too_long(self):
        response = self.client.post("/api/v1/amenities/", json={
            "name": "x" * 51,
        })
        self.assertEqual(response.status_code, 400)

    # ---------- GET /api/v1/amenities/ ----------

    def test_get_all_amenities(self):
        create_amenity(self.client)
        response = self.client.get("/api/v1/amenities/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    # ---------- GET /api/v1/amenities/<id> ----------

    def test_get_amenity_by_id_success(self):
        _, created = create_amenity(self.client)
        response = self.client.get(f"/api/v1/amenities/{created['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], created["name"])

    def test_get_amenity_not_found(self):
        response = self.client.get("/api/v1/amenities/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/amenities/<id> ----------

    def test_update_amenity_success(self):
        _, created = create_amenity(self.client)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": "Updated-" + unique_suffix(),
        })
        self.assertEqual(response.status_code, 200)

    def test_update_amenity_not_found(self):
        response = self.client.put("/api/v1/amenities/does-not-exist", json={
            "name": "Ghost Amenity",
        })
        self.assertEqual(response.status_code, 404)

    def test_update_amenity_invalid_empty_name(self):
        _, created = create_amenity(self.client)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": "",
        })
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
