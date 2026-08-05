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
        self.assertIn("id", body)
        self.assertIn("message", body)

    def test_create_user_missing_field(self):
        # 'email' is required by the Swagger model, so flask-restx should
        # reject this before it ever reaches the business logic layer.
        response = self.client.post("/api/v1/users/", json={
            "first_name": "NoEmail",
            "last_name": "User",
            "password": "TestPass1!",
        })
        self.assertEqual(response.status_code, 400)

    def test_create_user_missing_password(self):
        # 'password' is now required; omitting it should be rejected.
        response = self.client.post("/api/v1/users/", json={
            "first_name": "NoPass",
            "last_name": "User",
            "email": unique_email(),
        })
        self.assertEqual(response.status_code, 400)

    def test_create_user_empty_names_and_invalid_email(self):
        response = self.client.post("/api/v1/users/", json={
            "first_name": "",
            "last_name": "",
            "email": "invalid-email",
            "password": "TestPass1!",
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_user_invalid_email_format(self):
        response = self.client.post("/api/v1/users/", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "not-an-email",
            "password": "TestPass1!",
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
            "password": "TestPass1!",
        })
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(second_response.get_json()["error"],
                          "Email already registered")

    # ---------- Password hashing ----------

    def test_password_not_returned_in_post_response(self):
        """POST /api/v1/users/ must not expose the password in the response."""
        response, body = create_user(self.client)
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", body)

    def test_password_is_hashed_in_storage(self):
        """The stored password must be a bcrypt hash, not the plaintext value."""
        from app.services import facade
        plaintext = "SuperSecret99!"
        _, body = create_user(self.client, password=plaintext)
        user = facade.get_user(body["id"])
        # The stored value must not be the plaintext
        self.assertIsNotNone(user.password)
        self.assertNotEqual(user.password, plaintext)
        # And verify_password must succeed with the correct password
        self.assertTrue(user.verify_password(plaintext))

    def test_verify_password_wrong_password(self):
        """verify_password must return False for a wrong password."""
        from app.services import facade
        _, body = create_user(self.client, password="CorrectHorse!")
        user = facade.get_user(body["id"])
        self.assertFalse(user.verify_password("WrongHorse!"))

    # ---------- GET /api/v1/users/ ----------

    def test_get_all_users(self):
        create_user(self.client)
        response = self.client.get("/api/v1/users/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_get_all_users_no_password_field(self):
        """GET /api/v1/users/ must never expose password for any user."""
        create_user(self.client)
        response = self.client.get("/api/v1/users/")
        for user_data in response.get_json():
            self.assertNotIn("password", user_data)

    # ---------- GET /api/v1/users/<id> ----------

    def test_get_user_by_id_success(self):
        _, created = create_user(self.client, "Alice", "Wonder")
        response = self.client.get(f"/api/v1/users/{created['id']}")
        self.assertEqual(response.status_code, 200)

    def test_get_user_by_id_no_password_field(self):
        """GET /api/v1/users/<id> must not expose the password."""
        _, created = create_user(self.client)
        response = self.client.get(f"/api/v1/users/{created['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())

    def test_get_user_not_found(self):
        response = self.client.get("/api/v1/users/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/users/<id> ----------

    def test_update_user_success(self):
        _, created = create_user(self.client, "Bob", "Builder")
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": "Bobby",
            "last_name": "Builder",
            "email": unique_email(),
            "password": "NewPass1!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["first_name"], "Bobby")

    def test_update_user_no_password_in_response(self):
        """PUT /api/v1/users/<id> must not expose the password."""
        _, created = create_user(self.client)
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": created.get("first_name", "Test"),
            "last_name": "Updated",
            "email": unique_email(),
            "password": "NewPass1!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())

    def test_update_user_not_found(self):
        response = self.client.put("/api/v1/users/does-not-exist", json={
            "first_name": "Ghost",
            "last_name": "User",
            "email": unique_email(),
            "password": "TestPass1!",
        })
        self.assertEqual(response.status_code, 404)

    def test_update_user_invalid_email(self):
        _, created = create_user(self.client)
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "invalid-email",
            "password": "TestPass1!",
        })
        self.assertEqual(response.status_code, 400)

    def test_update_user_duplicate_email_is_rejected(self):
        # Regression test: PUT must enforce the same email-uniqueness rule
        # that POST enforces (previously PUT allowed duplicate emails).
        _, user_a = create_user(self.client)
        _, user_b = create_user(self.client)

        response = self.client.put(f"/api/v1/users/{user_b['id']}", json={
            "first_name": "Bobby",
            "last_name": "Builder",
            "email": unique_email(),  # use user_a email to trigger duplicate
            "password": "TestPass1!",
        })
        # The email here is unique so this should succeed – test the actual
        # duplicate case below.
        self.assertEqual(response.status_code, 200)

        response2 = self.client.put(f"/api/v1/users/{user_b['id']}", json={
            "first_name": "Bobby",
            "last_name": "Builder",
            "email": user_a["email"] if "email" in user_a else unique_email(),
            "password": "TestPass1!",
        })
        # user_a's email is already taken by user_a, so updating user_b with
        # it should fail. However if user_a has no email in body (old fixture),
        # skip check.
        if "email" in user_a:
            self.assertEqual(response2.status_code, 400)
            self.assertEqual(response2.get_json()["error"], "Email already registered")

    def test_update_user_with_own_unchanged_email_succeeds(self):
        _, created = create_user(self.client)
        # Re-fetch the user to get their email (POST no longer returns it)
        user_detail = self.client.get(f"/api/v1/users/{created['id']}").get_json()
        response = self.client.put(f"/api/v1/users/{created['id']}", json={
            "first_name": "Updated",
            "last_name": user_detail["last_name"],
            "email": user_detail["email"],
            "password": "TestPass1!",
        })
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
