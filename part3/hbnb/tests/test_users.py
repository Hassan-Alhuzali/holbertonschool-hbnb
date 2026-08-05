import unittest

from app import create_app
from tests.helpers import create_user, unique_email


class TestUserEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    # ---------- POST /api/v1/users/ ----------

    def test_create_user_success(self):
        response, body = create_user(self.client, "Jane", "Doe")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["first_name"], "Jane")
        self.assertEqual(body["last_name"], "Doe")
        self.assertIn("id", body)

    def test_create_user_missing_field(self):
        # 'email' is required by the Swagger model, so flask-restx should
        # reject this before it ever reaches the business logic layer.
        response = self.client.post("/api/v1/users/", json={
            "first_name": "NoEmail",
            "last_name": "User",
        })
        self.assertEqual(response.status_code, 400)

    def test_create_user_empty_names_and_invalid_email(self):
        response = self.client.post("/api/v1/users/", json={
            "first_name": "",
            "last_name": "",
            "email": "invalid-email",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_user_invalid_email_format(self):
        response = self.client.post("/api/v1/users/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "not-an-email",
        })
        self.assertEqual(response.status_code, 400)

    def test_create_user_duplicate_email(self):
        email = unique_email()
        first_response, _ = create_user(self.client, email=email)
        self.assertEqual(first_response.status_code, 201)

        second_response = self.client.post("/api/v1/users/", json={
            "first_name": "Another",
            "last_name": "Person",
            "email": email,
        })
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(second_response.get_json()["error"],
                          "Email already registered")

    # ---------- GET /api/v1/users/ ----------

    def test_get_all_users(self):
        create_user(self.client)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    # ---------- GET /api/v1/users/<id> ----------

    def test_get_user_by_id_success(self):
        _, created = create_user(self.client, "Alice", "Wonder")
        response = self.client.get(f"/api/v1/users/{created['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], created["email"])

    def test_get_user_not_found(self):
        response = self.client.get("/api/v1/users/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/users/<id> ----------

    def test_update_user_success(self):
        _, created = create_user(self.client, "Bob", "Builder")
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": "Bobby",
            "last_name": "Builder",
            "email": created["email"],
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["first_name"], "Bobby")

    def test_update_user_not_found(self):
        response = self.client.put("/api/v1/users/does-not-exist", json={
            "first_name": "Ghost",
            "last_name": "User",
            "email": unique_email(),
        })
        self.assertEqual(response.status_code, 404)

    def test_update_user_invalid_email(self):
        _, created = create_user(self.client)
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": created["first_name"],
            "last_name": created["last_name"],
            "email": "invalid-email",
        })
        self.assertEqual(response.status_code, 400)

    def test_update_user_duplicate_email_is_rejected(self):
        # Regression test: PUT must enforce the same email-uniqueness rule
        # that POST enforces (previously PUT allowed duplicate emails).
        _, user_a = create_user(self.client)
        _, user_b = create_user(self.client)

        response = self.client.put(f"/api/v1/users/{user_b['id']}", json={
            "first_name": user_b["first_name"],
            "last_name": user_b["last_name"],
            "email": user_a["email"],
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "Email already registered")

    def test_update_user_with_own_unchanged_email_succeeds(self):
        _, created = create_user(self.client)
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": "Updated",
            "last_name": created["last_name"],
            "email": created["email"],
        })
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
