"""Tests for Task 04 – Authenticated User Access Endpoints.

Covers every rule stated in task_04_auth_access.md:

Places
------
- POST /api/v1/places/       requires JWT; owner_id is auto-set from token
- PUT  /api/v1/places/<id>   requires JWT; only the owner may update
- GET  /api/v1/places/       public (no token needed)
- GET  /api/v1/places/<id>   public (no token needed)

Reviews
-------
- POST   /api/v1/reviews/       requires JWT; users cannot review their own
                                place; one review per user per place
- PUT    /api/v1/reviews/<id>   requires JWT; only the original reviewer may update
- DELETE /api/v1/reviews/<id>   requires JWT; only the original reviewer may delete

Users
-----
- PUT /api/v1/users/<id>   requires JWT; users may only update their own record;
                           email and password cannot be changed here
"""

import unittest

from app import create_app
from tests.helpers import create_user_and_login, create_place, create_review


PASSWORD = "TestPass1!"


class TestPlaceAuthAccess(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.owner, self.owner_token = create_user_and_login(self.client)
        self.other, self.other_token = create_user_and_login(self.client)

    # ------------------------------------------------------------------
    # POST /api/v1/places/
    # ------------------------------------------------------------------

    def test_create_place_requires_token(self):
        """POST /api/v1/places/ without a JWT must return 401."""
        response = self.client.post("/api/v1/places/", json={
            "title": "Unauthenticated Place",
            "price": 50.0,
            "latitude": 10.0,
            "longitude": 10.0,
        })
        self.assertEqual(response.status_code, 401)

    def test_create_place_owner_id_set_from_jwt(self):
        """The created place's owner must be the authenticated user, not any
        owner_id that may be supplied in the body."""
        response, body = create_place(self.client, self.owner_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["owner_id"], self.owner["id"])

    # ------------------------------------------------------------------
    # PUT /api/v1/places/<id>
    # ------------------------------------------------------------------

    def test_update_place_requires_token(self):
        """PUT /api/v1/places/<id> without a JWT must return 401."""
        _, place = create_place(self.client, self.owner_token)
        response = self.client.put(f"/api/v1/places/{place['id']}", json={
            "title": "Sneaky Update",
        })
        self.assertEqual(response.status_code, 401)

    def test_owner_can_update_own_place(self):
        """The place owner may successfully update the place."""
        _, place = create_place(self.client, self.owner_token)
        response = self.client.put(f"/api/v1/places/{place['id']}", json={
            "title": "Owner Updated Title",
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 200)

    def test_non_owner_cannot_update_place(self):
        """A user who does not own the place must get 403."""
        _, place = create_place(self.client, self.owner_token)
        response = self.client.put(f"/api/v1/places/{place['id']}", json={
            "title": "Hijacked Title",
        }, headers={"Authorization": f"Bearer {self.other_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    # ------------------------------------------------------------------
    # Public place endpoints
    # ------------------------------------------------------------------

    def test_get_all_places_is_public(self):
        """GET /api/v1/places/ must work without any token."""
        response = self.client.get("/api/v1/places/")
        self.assertEqual(response.status_code, 200)

    def test_get_place_detail_is_public(self):
        """GET /api/v1/places/<id> must work without any token."""
        _, place = create_place(self.client, self.owner_token)
        response = self.client.get(f"/api/v1/places/{place['id']}")
        self.assertEqual(response.status_code, 200)


class TestReviewAuthAccess(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.owner, self.owner_token = create_user_and_login(self.client)
        self.reviewer, self.reviewer_token = create_user_and_login(self.client)
        self.other, self.other_token = create_user_and_login(self.client)
        _, self.place = create_place(self.client, self.owner_token)

    # ------------------------------------------------------------------
    # POST /api/v1/reviews/
    # ------------------------------------------------------------------

    def test_create_review_requires_token(self):
        """POST /api/v1/reviews/ without a JWT must return 401."""
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Great place!",
            "rating": 5,
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 401)

    def test_reviewer_can_create_review(self):
        """An authenticated user who does not own the place may leave a review."""
        response, body = create_review(
            self.client, self.place["id"], self.reviewer_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["place_id"], self.place["id"])
        self.assertEqual(body["user_id"], self.reviewer["id"])

    def test_owner_cannot_review_own_place(self):
        """The owner of a place must not be able to review it (400)."""
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Self-review attempt",
            "rating": 5,
            "place_id": self.place["id"],
        }, headers={"Authorization": f"Bearer {self.owner_token}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "You cannot review your own place")

    def test_duplicate_review_is_rejected(self):
        """A user may not review the same place twice (400)."""
        create_review(self.client, self.place["id"], self.reviewer_token)
        response, body = create_review(
            self.client, self.place["id"], self.reviewer_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["error"], "You have already reviewed this place")

    def test_review_user_id_set_from_jwt(self):
        """The review's user_id must match the JWT identity, not any user_id
        that may be included in the request body."""
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Legit review",
            "rating": 4,
            "place_id": self.place["id"],
        }, headers={"Authorization": f"Bearer {self.reviewer_token}"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["user_id"], self.reviewer["id"])

    # ------------------------------------------------------------------
    # PUT /api/v1/reviews/<id>
    # ------------------------------------------------------------------

    def test_update_review_requires_token(self):
        """PUT /api/v1/reviews/<id> without a JWT must return 401."""
        _, review = create_review(
            self.client, self.place["id"], self.reviewer_token)
        response = self.client.put(f"/api/v1/reviews/{review['id']}", json={
            "text": "Stealth update",
            "rating": 2,
        })
        self.assertEqual(response.status_code, 401)

    def test_reviewer_can_update_own_review(self):
        """The original reviewer may successfully update their review."""
        _, review = create_review(
            self.client, self.place["id"], self.reviewer_token)
        response = self.client.put(f"/api/v1/reviews/{review['id']}", json={
            "text": "Updated opinion",
            "rating": 3,
        }, headers={"Authorization": f"Bearer {self.reviewer_token}"})
        self.assertEqual(response.status_code, 200)

    def test_non_reviewer_cannot_update_review(self):
        """A user who did not create the review must get 403."""
        _, review = create_review(
            self.client, self.place["id"], self.reviewer_token)
        response = self.client.put(f"/api/v1/reviews/{review['id']}", json={
            "text": "Hijacked update",
            "rating": 1,
        }, headers={"Authorization": f"Bearer {self.other_token}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    # ------------------------------------------------------------------
    # DELETE /api/v1/reviews/<id>
    # ------------------------------------------------------------------

    def test_delete_review_requires_token(self):
        """DELETE /api/v1/reviews/<id> without a JWT must return 401."""
        _, review = create_review(
            self.client, self.place["id"], self.reviewer_token)
        response = self.client.delete(f"/api/v1/reviews/{review['id']}")
        self.assertEqual(response.status_code, 401)

    def test_reviewer_can_delete_own_review(self):
        """The original reviewer may successfully delete their review."""
        _, review = create_review(
            self.client, self.place["id"], self.reviewer_token)
        response = self.client.delete(
            f"/api/v1/reviews/{review['id']}",
            headers={"Authorization": f"Bearer {self.reviewer_token}"}
        )
        self.assertEqual(response.status_code, 200)
        # Verify it is actually gone.
        follow_up = self.client.get(f"/api/v1/reviews/{review['id']}")
        self.assertEqual(follow_up.status_code, 404)

    def test_non_reviewer_cannot_delete_review(self):
        """A user who did not create the review must get 403 on delete."""
        _, review = create_review(
            self.client, self.place["id"], self.reviewer_token)
        response = self.client.delete(
            f"/api/v1/reviews/{review['id']}",
            headers={"Authorization": f"Bearer {self.other_token}"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")


class TestUserAuthAccess(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.user_a, self.token_a = create_user_and_login(self.client)
        self.user_b, self.token_b = create_user_and_login(self.client)

    # ------------------------------------------------------------------
    # PUT /api/v1/users/<id>
    # ------------------------------------------------------------------

    def test_update_user_requires_token(self):
        """PUT /api/v1/users/<id> without a JWT must return 401."""
        response = self.client.put(f"/api/v1/users/{self.user_a['id']}", json={
            "first_name": "Ghost",
            "last_name": "Update",
        })
        self.assertEqual(response.status_code, 401)

    def test_user_can_update_own_profile(self):
        """An authenticated user may update their own first_name / last_name."""
        response = self.client.put(f"/api/v1/users/{self.user_a['id']}", json={
            "first_name": "NewFirst",
            "last_name": "NewLast",
        }, headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["first_name"], "NewFirst")
        self.assertEqual(body["last_name"], "NewLast")

    def test_user_cannot_update_another_users_profile(self):
        """Token owner A must not be able to update user B's profile (403)."""
        response = self.client.put(f"/api/v1/users/{self.user_b['id']}", json={
            "first_name": "Hijacked",
            "last_name": "Name",
        }, headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"], "Unauthorized action")

    def test_update_user_email_is_rejected(self):
        """Including 'email' in the PUT body must return 400."""
        response = self.client.put(f"/api/v1/users/{self.user_a['id']}", json={
            "first_name": "John",
            "email": "changed@example.com",
        }, headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "You cannot modify email or password")

    def test_update_user_password_is_rejected(self):
        """Including 'password' in the PUT body must return 400."""
        response = self.client.put(f"/api/v1/users/{self.user_a['id']}", json={
            "first_name": "John",
            "password": "NewPassword99!",
        }, headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"],
                          "You cannot modify email or password")

    def test_update_user_response_excludes_password(self):
        """A successful PUT must never expose the password in the response."""
        response = self.client.put(f"/api/v1/users/{self.user_a['id']}", json={
            "first_name": "Safe",
            "last_name": "Response",
        }, headers={"Authorization": f"Bearer {self.token_a}"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("password", response.get_json())


if __name__ == "__main__":
    unittest.main()
