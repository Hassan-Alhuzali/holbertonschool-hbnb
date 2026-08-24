"""Tests for Task 05 – Administrator Access Endpoints.

Covers every rule stated in task_05_admin_access.md:

Users (admin-only write access)
--------------------------------
- POST /api/v1/users/       401 without token; 403 for non-admins; 201 for admins
- PUT  /api/v1/users/<id>   admins bypass ownership and may change email & password

Amenities (admin-only write access)
--------------------------------------
- POST /api/v1/amenities/       401 without token; 403 for non-admins; 201 for admins
- PUT  /api/v1/amenities/<id>   401 without token; 403 for non-admins; 200 for admins

Places (admin bypasses ownership on PUT)
------------------------------------------
- PUT /api/v1/places/<id>   admins may update any place regardless of ownership

Reviews (admin bypasses ownership on PUT and DELETE)
------------------------------------------------------
- PUT    /api/v1/reviews/<id>   admins may update any review
- DELETE /api/v1/reviews/<id>   admins may delete any review
"""

import unittest

from app import create_app
from tests.helpers import (
    create_admin_and_login,
    create_user_and_login,
    create_user,
    create_amenity,
    create_place,
    create_review,
    unique_email,
    unique_suffix,
)


class TestAdminUserEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        # Admin created directly via the facade (cannot use the restricted API for bootstrap).
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        # Regular user for non-admin permission checks.
        self.user, self.user_token = create_user_and_login(self.client, self.app)

    # ------------------------------------------------------------------
    # POST /api/v1/users/
    # ------------------------------------------------------------------

    def test_admin_can_create_user(self):
        """Admin should receive 201 when creating a new user."""
        response, body = create_user(self.client, admin_token=self.admin_token)
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

    def test_non_admin_cannot_create_user(self):
        """POST /api/v1/users/ with a non-admin JWT must return 403."""
        response = self.client.post("/api/v1/users/", json={
            "first_name": "Non",
            "last_name": "Admin",
            "email": unique_email(),
            "password": "TestPass1!",
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Admin privileges required")

    def test_admin_create_user_duplicate_email_returns_400(self):
        """Admin creating a user with a duplicate email must get 400."""
        email = unique_email()
        r1, _ = create_user(self.client, email=email, admin_token=self.admin_token)
        self.assertEqual(r1.status_code, 201)
        r2, body = create_user(self.client, email=email, admin_token=self.admin_token)
        self.assertEqual(r2.status_code, 400)
        self.assertEqual(body["error"], "Email already registered")

    def test_admin_create_user_no_password_in_response(self):
        """POST /api/v1/users/ must not expose the password field in the response."""
        _, body = create_user(self.client, admin_token=self.admin_token)
        self.assertNotIn("password", body)

    # ------------------------------------------------------------------
    # PUT /api/v1/users/<id>
    # ------------------------------------------------------------------

    def test_admin_can_update_any_user_name(self):
        """Admin may update another user's first_name and last_name."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "AdminUpdated",
            "last_name": "ByAdmin",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["first_name"], "AdminUpdated")
        self.assertEqual(body["last_name"], "ByAdmin")

    def test_admin_can_update_user_email(self):
        """Admin may change another user's email."""
        new_email = unique_email()
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "email": new_email,
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], new_email)

    def test_admin_can_update_user_password(self):
        """Admin may change another user's password; the user can then log in with it."""
        new_password = "NewAdminSet99!"
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "password": new_password,
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

        # Verify the user can authenticate with the new password.
        login_resp = self.client.post("/api/v1/auth/login", json={
            "email": self.user["email"],
            "password": new_password,
        })
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn("access_token", login_resp.get_json())

    def test_admin_update_user_duplicate_email_returns_400(self):
        """Admin trying to assign an already-used email to another user must get 400."""
        other, _ = create_user_and_login(self.client, self.app)
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "email": other["email"],
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Email already in use")

    def test_admin_update_user_same_email_allowed(self):
        """Admin assigning a user their own current email must succeed (not a duplicate)."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "email": self.user["email"],
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

    def test_admin_update_response_excludes_password(self):
        """Admin PUT must never expose the password in the response."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "first_name": "Safe",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())

    def test_non_admin_email_change_still_blocked(self):
        """Regular users must still be blocked from changing their own email (400)."""
        response = self.client.put(f"/api/v1/users/{self.user['id']}", json={
            "email": unique_email(),
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "You cannot modify email or password")

    def test_non_admin_cannot_update_other_user(self):
        """Regular users must still be blocked from updating other users' records (403)."""
        response = self.client.put(f"/api/v1/users/{self.admin['id']}", json={
            "first_name": "Hacked",
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")


class TestAdminAmenityEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        self.user, self.user_token = create_user_and_login(self.client, self.app)

    # ------------------------------------------------------------------
    # POST /api/v1/amenities/
    # ------------------------------------------------------------------

    def test_admin_can_create_amenity(self):
        """Admin should receive 201 when creating a new amenity."""
        response, body = create_amenity(self.client, self.admin_token,
                                         name=f"Pool-{unique_suffix()}")
        self.assertEqual(response.status_code, 201)
        self.assertIn("id", body)
        self.assertIn("name", body)

    def test_create_amenity_without_token_returns_401(self):
        """POST /api/v1/amenities/ without a JWT must return 401."""
        response = self.client.post("/api/v1/amenities/", json={"name": "Wi-Fi"})
        self.assertEqual(response.status_code, 401)

    def test_non_admin_cannot_create_amenity(self):
        """POST /api/v1/amenities/ with a non-admin JWT must return 403."""
        response = self.client.post("/api/v1/amenities/", json={
            "name": f"Sauna-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Admin privileges required")

    # ------------------------------------------------------------------
    # PUT /api/v1/amenities/<id>
    # ------------------------------------------------------------------

    def test_admin_can_update_amenity(self):
        """Admin should receive 200 when updating an existing amenity."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": f"Updated-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

    def test_update_amenity_without_token_returns_401(self):
        """PUT /api/v1/amenities/<id> without a JWT must return 401."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": "Sneaky Update",
        })
        self.assertEqual(response.status_code, 401)

    def test_non_admin_cannot_update_amenity(self):
        """PUT /api/v1/amenities/<id> with a non-admin JWT must return 403."""
        _, created = create_amenity(self.client, self.admin_token)
        response = self.client.put(f"/api/v1/amenities/{created['id']}", json={
            "name": f"NonAdmin-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.user_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Admin privileges required")


class TestAdminPlaceBypass(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        self.owner, self.owner_token = create_user_and_login(self.client, self.app)
        _, self.place = create_place(self.client, self.owner_token)

    def test_admin_can_update_any_place(self):
        """Admin must be able to update a place they do not own."""
        response = self.client.put(f"/api/v1/places/{self.place['id']}", json={
            "title": f"Admin Renamed-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

    def test_admin_can_update_place_price(self):
        """Admin may change any numeric field on any place."""
        response = self.client.put(f"/api/v1/places/{self.place['id']}", json={
            "price": 999.0,
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

    def test_non_owner_regular_user_still_blocked(self):
        """A non-admin non-owner must still receive 403."""
        other, other_token = create_user_and_login(self.client, self.app)
        response = self.client.put(f"/api/v1/places/{self.place['id']}", json={
            "title": "Hijack Attempt",
        }, headers={"Authorization": f"Bearer {other_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    def test_owner_can_still_update_own_place(self):
        """The original owner must still be able to update their place."""
        response = self.client.put(f"/api/v1/places/{self.place['id']}", json={
            "title": f"Owner Updated-{unique_suffix()}",
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 200)


class TestAdminReviewBypass(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.admin, self.admin_token = create_admin_and_login(self.client, self.app)
        self.owner, self.owner_token = create_user_and_login(self.client, self.app)
        self.reviewer, self.reviewer_token = create_user_and_login(self.client, self.app)
        _, self.place = create_place(self.client, self.owner_token)
        _, self.review = create_review(
            self.client, self.place["id"], self.reviewer_token)

    def test_admin_can_update_any_review(self):
        """Admin must be able to update a review they did not write."""
        response = self.client.put(f"/api/v1/reviews/{self.review['id']}", json={
            "text": "Admin corrected this review",
            "rating": 3,
        }, headers={"Authorization": f"Bearer {self.admin_token}"})
        self.assertEqual(response.status_code, 200)

    def test_admin_can_delete_any_review(self):
        """Admin must be able to delete a review they did not write."""
        response = self.client.delete(
            f"/api/v1/reviews/{self.review['id']}",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        self.assertEqual(response.status_code, 200)
        follow_up = self.client.get(f"/api/v1/reviews/{self.review['id']}")
        self.assertEqual(follow_up.status_code, 404)

    def test_non_reviewer_regular_user_still_blocked_on_put(self):
        """A non-admin user who did not write the review must still get 403 on PUT."""
        other, other_token = create_user_and_login(self.client, self.app)
        response = self.client.put(f"/api/v1/reviews/{self.review['id']}", json={
            "text": "Hijack attempt",
            "rating": 1,
        }, headers={"Authorization": f"Bearer {other_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    def test_non_reviewer_regular_user_still_blocked_on_delete(self):
        """A non-admin user who did not write the review must still get 403 on DELETE."""
        other, other_token = create_user_and_login(self.client, self.app)
        response = self.client.delete(
            f"/api/v1/reviews/{self.review['id']}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    def test_reviewer_can_still_update_own_review(self):
        """The original reviewer must still be able to update their own review."""
        response = self.client.put(f"/api/v1/reviews/{self.review['id']}", json={
            "text": "I changed my mind",
            "rating": 4,
        }, headers={"Authorization": f"Bearer {self.reviewer_token}"})
        self.assertEqual(response.status_code, 200)

    def test_reviewer_can_still_delete_own_review(self):
        """The original reviewer must still be able to delete their own review."""
        response = self.client.delete(
            f"/api/v1/reviews/{self.review['id']}",
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
