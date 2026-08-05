"""Tests for JWT authentication endpoints.

Covers:
- POST /api/v1/auth/login  – login and token issuance
- GET  /api/v1/auth/protected – protected endpoint access
"""

import unittest

from app import create_app
from tests.helpers import create_user, unique_email


PASSWORD = "TestPass1!"


class TestAuthLogin(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _register_and_login(self, password=PASSWORD):
        """Create a user and return their JWT access token."""
        email = unique_email()
        create_user(self.client, email=email, password=password)
        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password,
        })
        return response, response.get_json()

    # ------------------------------------------------------------------
    # POST /api/v1/auth/login – success cases
    # ------------------------------------------------------------------

    def test_login_returns_200_and_access_token(self):
        """Valid credentials must yield HTTP 200 and an access_token."""
        response, body = self._register_and_login()
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", body)
        self.assertIsInstance(body["access_token"], str)
        self.assertTrue(len(body["access_token"]) > 0)

    def test_login_token_is_non_empty_string(self):
        """The access_token value must be a non-empty JWT string."""
        _, body = self._register_and_login()
        token = body.get("access_token", "")
        # A valid JWT has three dot-separated parts
        self.assertEqual(len(token.split(".")), 3,
                         "access_token does not look like a JWT")

    # ------------------------------------------------------------------
    # POST /api/v1/auth/login – failure cases
    # ------------------------------------------------------------------

    def test_login_wrong_password_returns_401(self):
        """A wrong password must result in HTTP 401."""
        email = unique_email()
        create_user(self.client, email=email, password=PASSWORD)
        response = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": "WrongPassword!",
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.get_json())

    def test_login_unknown_email_returns_401(self):
        """An email that was never registered must result in HTTP 401."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": PASSWORD,
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.get_json())

    def test_login_missing_email_returns_400(self):
        """Omitting the email field must be rejected by input validation."""
        response = self.client.post("/api/v1/auth/login", json={
            "password": PASSWORD,
        })
        self.assertEqual(response.status_code, 400)

    def test_login_missing_password_returns_400(self):
        """Omitting the password field must be rejected by input validation."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": unique_email(),
        })
        self.assertEqual(response.status_code, 400)

    def test_login_empty_body_returns_400(self):
        """An empty JSON body must be rejected."""
        response = self.client.post("/api/v1/auth/login", json={})
        self.assertEqual(response.status_code, 400)

    # ------------------------------------------------------------------
    # GET /api/v1/auth/protected – access control
    # ------------------------------------------------------------------

    def test_protected_with_valid_token_returns_200(self):
        """A valid JWT must grant access to the protected endpoint."""
        _, login_body = self._register_and_login()
        token = login_body["access_token"]
        response = self.client.get(
            "/api/v1/auth/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertIn("message", body)
        self.assertIn("Hello, user", body["message"])

    def test_protected_without_token_returns_401(self):
        """Missing Authorization header must be rejected with HTTP 401."""
        response = self.client.get("/api/v1/auth/protected")
        self.assertEqual(response.status_code, 401)

    def test_protected_with_invalid_token_returns_422(self):
        """A malformed / tampered token must be rejected (422 Unprocessable)."""
        response = self.client.get(
            "/api/v1/auth/protected",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        # flask-jwt-extended returns 422 for structurally invalid tokens
        self.assertIn(response.status_code, (401, 422))

    def test_protected_response_contains_user_id(self):
        """The protected endpoint must echo back the authenticated user's id."""
        email = unique_email()
        _, created = create_user(self.client, email=email, password=PASSWORD)
        user_id = created["id"]

        login_resp = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": PASSWORD,
        })
        token = login_resp.get_json()["access_token"]

        response = self.client.get(
            "/api/v1/auth/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(user_id, response.get_json()["message"])

    # ------------------------------------------------------------------
    # Token claims
    # ------------------------------------------------------------------

    def test_regular_user_is_admin_claim_is_false(self):
        """is_admin claim in the protected response must be False for a regular user."""
        _, login_body = self._register_and_login()
        token = login_body["access_token"]
        response = self.client.get(
            "/api/v1/auth/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["is_admin"])


if __name__ == "__main__":
    unittest.main()
