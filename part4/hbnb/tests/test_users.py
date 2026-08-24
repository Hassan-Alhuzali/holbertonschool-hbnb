import unittest

from app import create_app
from tests.helpers import (
    create_admin_and_login,
    create_user,
    create_user_and_login,
    create_user_direct,
    unique_email,
)


class TestUserEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Admin is created via the facade (bypasses the now-restricted POST /users/).
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        # Regular user for PUT tests.
        self.user, self.token = create_user_and_login(self.client, self.app)

    # ---------- POST /api/v1/users/ ----------

    def test_create_user_success(self):
        """Admin can create a new user."""
        response, body = create_user(self.client, "Jane", "Doe",
                                      admin_token=self.admin_token)
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", body)
        self.assertIn("message", body)

    def test_create_user_without_token_returns_401(self):
        """POST /api/v1/users/ without a JWT must return 401."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "No",
            "last_name": "Token",
            "email": unique_email(),
            "password": "TestPass1!",
        })
        self.assertEqual(response.status_code, 401)

    def test_create_user_non_admin_returns_403(self):
        """POST /api/v1/users/ with a non-admin JWT must return 403."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "Non",
            "last_name": "Admin",
            "email": unique_email(),
            "password": "TestPass1!",
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Admin privileges required")

    def test_create_user_missing_field(self):
        """Admin POST with missing 'email' field must return 400."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "NoEmail",
            "last_name": "User",
            "password": "TestPass1!",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_user_missing_password(self):
        """Admin POST with missing 'password' field must return 400."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "NoPass",
            "last_name": "User",
            "email": unique_email(),
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_user_empty_names_and_invalid_email(self):
        """Admin POST with empty names and invalid email must return 400."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "",
            "last_name": "",
            "email": "invalid-email",
            "password": "TestPass1!",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_user_invalid_email_format(self):
        """Admin POST with a malformed email must return 400."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "not-an-email",
            "password": "TestPass1!",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)

    def test_create_user_duplicate_email(self):
        """Admin POST with a duplicate email must return 400."""
        email = unique_email()
        first_response, _ = create_user(self.client, email=email,
                                         admin_token=self.admin_token)
        self.assertEqual(first_response.status_code, 201)

        second_response = self.client.post("/api/v1/users/", json={
            "first_name": "Another",
            "last_name": "Person",
            "email": email,
            "password": "TestPass1!",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(second_response.get_json()["error"],
                          "Email already registered")

    # ---------- Password hashing ----------

    def test_password_not_returned_in_post_response(self):
        """POST /api/v1/users/ must not expose the password in the response."""
        response, body = create_user(self.client, admin_token=self.admin_token)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", body)

    def test_password_is_hashed_in_storage(self):
        """The stored password must be a bcrypt hash, not the plaintext value."""
        from app.services import facade
        plaintext = "SuperSecret99!"
        _, body = create_user(self.client, password=plaintext,
                               admin_token=self.admin_token)
        user = facade.get_user(body["id"])
        self.assertIsNotNone(user.password)
        self.assertNotEqual(user.password, plaintext)
        self.assertTrue(user.verify_password(plaintext))

    def test_verify_password_wrong_password(self):
        """verify_password must return False for a wrong password."""
        from app.services import facade
        _, body = create_user(self.client, password="CorrectHorse!",
                               admin_token=self.admin_token)
        user = facade.get_user(body["id"])
        self.assertFalse(user.verify_password("WrongHorse!"))

    # ---------- GET /api/v1/users/ ----------

    def test_get_all_users(self):
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_get_all_users_no_password_field(self):
        """GET /api/v1/users/ must never expose password for any user."""
        response = self.client.get("/api/v1/users/")
        for user_data in response.get_json():
            self.assertNotIn("password", user_data)

    # ---------- GET /api/v1/users/<id> ----------

    def test_get_user_by_id_success(self):
        _, body = create_user(self.client, "Alice", "Wonder",
                               admin_token=self.admin_token)
        response = self.client.get(f"/api/v1/users/{body['id']}")
        self.assertEqual(response.status_code, 200)

    def test_get_user_by_id_no_password_field(self):
        """GET /api/v1/users/<id> must not expose the password."""
        _, created = create_user(self.client, admin_token=self.admin_token)
        response = self.client.get(f"/api/v1/users/{created['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())

    def test_get_user_not_found(self):
        response = self.client.get("/api/v1/users/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/users/<id> ----------

    def test_update_user_success(self):
        """Users can update their own first_name and last_name."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "Bobby",
            "last_name": "Builder",
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["first_name"], "Bobby")

    def test_update_user_without_token_returns_401(self):
        """PUT /api/v1/users/<id> must require a JWT token."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "NoToken",
            "last_name": "User",
        })
        self.assertEqual(response.status_code, 401)

    def test_update_user_no_password_in_response(self):
        """PUT /api/v1/users/<id> must not expose the password."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "Updated",
            "last_name": "Name",
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())

    def test_update_other_user_returns_403(self):
        """Trying to update a different user's data must return 403."""
        other, _ = create_user_and_login(self.client, self.app)
        response = self.client.put(f"/api/v1/users/{other['id']}", json={
            "first_name": "Hijack",
            "last_name": "Attempt",
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    def test_update_user_email_blocked(self):
        """PUT must reject attempts by regular users to change email (400)."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "newemail@example.com",
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "You cannot modify email or password")

    def test_update_user_password_blocked(self):
        """PUT must reject attempts by regular users to change password (400)."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "John",
            "last_name": "Doe",
            "password": "NewSecret99!",
        }, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "You cannot modify email or password")


if __name__ == "__main__":
    unittest.main()
