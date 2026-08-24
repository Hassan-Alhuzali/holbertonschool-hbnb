import unittest

from app import create_app
from tests.helpers import create_admin_and_login, create_amenity, unique_suffix


class TestAmenityEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Admin is required for POST and PUT amenity endpoints.
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        # Regular user for 403 tests.
        from tests.helpers import create_user_and_login
        self.user, self.user_token = create_user_and_login(self.client, self.app)

    # ---------- POST /api/v1/amenities/ ----------

    def test_create_amenity_success(self):
        response, body = create_amenity(self.client, self.admin_token,
                                         "Wi-Fi-" + unique_suffix())
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", body)
        self.assertIn("name", body)

    def test_create_amenity_without_token_returns_401(self):
        """POST /api/v1/amenities/ without a JWT must return 401."""
        response = self.client.post("/api/v1/amenities/", json={"name": "Wi-Fi"})
        self.assertEqual(response.status_code, 401)

    def test_create_amenity_non_admin_returns_403(self):
        """POST /api/v1/amenities/ with a non-admin JWT must return 403."""
        response = self.client.post("/api/v1/amenities/", json={
            "name": f"Sauna-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Admin privileges required")

    def test_create_amenity_empty_name(self):
        """Admin POST with empty name must return 400."""
        response = self.client.post("/api/v1/amenities/", json={"name": ""},
                                     headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_amenity_missing_field(self):
        """Admin POST with missing name field must return 400."""
        response = self.client.post("/api/v1/amenities/", json={},
                                     headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_amenity_name_too_long(self):
        """Admin POST with a name exceeding the limit must return 400."""
        response = self.client.post("/api/v1/amenities/", json={
            "name": "x" * 51,
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)

    # ---------- GET /api/v1/amenities/ ----------

    def test_get_all_amenities(self):
        create_amenity(self.client, self.admin_token)
        response = self.client.get("/api/v1/amenities/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    # ---------- GET /api/v1/amenities/<id> ----------

    def test_get_amenity_by_id_success(self):
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.get(f"/api/v1/amenities/{created['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], created["name"])

    def test_get_amenity_not_found(self):
        response = self.client.get("/api/v1/amenities/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/amenities/<id> ----------

    def test_update_amenity_success(self):
        """Admin can update an amenity."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": "Updated-" + unique_suffix(),
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

    def test_update_amenity_without_token_returns_401(self):
        """PUT /api/v1/amenities/<id> without a JWT must return 401."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": "Ghost Amenity",
        })
        self.assertEqual(response.status_code, 401)

    def test_update_amenity_non_admin_returns_403(self):
        """PUT /api/v1/amenities/<id> with a non-admin JWT must return 403."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": f"NonAdmin-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Admin privileges required")

    def test_update_amenity_not_found(self):
        """Admin PUT on a non-existent amenity must return 404."""
        response = self.client.put("/api/v1/amenities/does-not-exist", json={
            "name": "Ghost Amenity",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 404)

    def test_update_amenity_invalid_empty_name(self):
        """Admin PUT with an empty name must return 400."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": "",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
