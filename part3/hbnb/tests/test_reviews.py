import unittest

from app import create_app
from tests.helpers import create_user, create_place, create_review


class TestReviewEndpoints(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        _, self.owner = create_user(self.client)
        _, self.reviewer = create_user(self.client)
        _, self.place = create_place(self.client, self.owner["id"])

    # ---------- POST /api/v1/reviews/ ----------

    def test_create_review_success(self):
        response, body = create_review(self.client, self.reviewer["id"], self.place["id"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(body["user_id"], self.reviewer["id"])
        self.assertEqual(body["place_id"], self.place["id"])

    def test_create_review_missing_field(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Missing rating",
            "user_id": self.reviewer["id"],
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_review_empty_text(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "",
            "rating": 3,
            "user_id": self.reviewer["id"],
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_review_rating_too_high(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Too high",
            "rating": 6,
            "user_id": self.reviewer["id"],
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_review_rating_too_low(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Too low",
            "rating": 0,
            "user_id": self.reviewer["id"],
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_review_rating_boundaries_are_valid(self):
        low, _ = create_review(self.client, self.reviewer["id"], self.place["id"], rating=1)
        high, _ = create_review(self.client, self.reviewer["id"], self.place["id"], rating=5)
        self.assertEqual(low.status_code, 201)
        self.assertEqual(high.status_code, 201)

    def test_create_review_rating_wrong_type(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Bad type",
            "rating": "five",
            "user_id": self.reviewer["id"],
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_review_nonexistent_user(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Ghost user",
            "rating": 3,
            "user_id": "does-not-exist",
            "place_id": self.place["id"],
        })
        self.assertEqual(response.status_code, 400)

    def test_create_review_nonexistent_place(self):
        response = self.client.post("/api/v1/reviews/", json={
            "text": "Ghost place",
            "rating": 3,
            "user_id": self.reviewer["id"],
            "place_id": "does-not-exist",
        })
        self.assertEqual(response.status_code, 400)

    # ---------- GET /api/v1/reviews/ ----------

    def test_get_all_reviews(self):
        create_review(self.client, self.reviewer["id"], self.place["id"])
        response = self.client.get("/api/v1/reviews/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    # ---------- GET /api/v1/reviews/<id> ----------

    def test_get_review_by_id_success(self):
        _, created = create_review(self.client, self.reviewer["id"], self.place["id"])
        response = self.client.get(f"/api/v1/reviews/{created['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["id"], created["id"])

    def test_get_review_not_found(self):
        response = self.client.get("/api/v1/reviews/does-not-exist")
        self.assertEqual(response.status_code, 404)

    # ---------- PUT /api/v1/reviews/<id> ----------

    def test_update_review_success(self):
        _, created = create_review(self.client, self.reviewer["id"], self.place["id"])
        response = self.client.put(f"/api/v1/reviews/{created['id']}", json={
            "text": "Updated text",
            "rating": 4,
        })
        self.assertEqual(response.status_code, 200)

    def test_update_review_not_found(self):
        response = self.client.put("/api/v1/reviews/does-not-exist", json={
            "text": "Ghost",
            "rating": 3,
        })
        self.assertEqual(response.status_code, 404)

    def test_update_review_invalid_rating(self):
        _, created = create_review(self.client, self.reviewer["id"], self.place["id"])
        response = self.client.put(f"/api/v1/reviews/{created['id']}", json={
            "rating": 10,
        })
        self.assertEqual(response.status_code, 400)

    # ---------- DELETE /api/v1/reviews/<id> ----------

    def test_delete_review_success(self):
        _, created = create_review(self.client, self.reviewer["id"], self.place["id"])
        response = self.client.delete(f"/api/v1/reviews/{created['id']}")
        self.assertEqual(response.status_code, 200)

        follow_up = self.client.get(f"/api/v1/reviews/{created['id']}")
        self.assertEqual(follow_up.status_code, 404)

    def test_delete_review_not_found(self):
        response = self.client.delete("/api/v1/reviews/does-not-exist")
        self.assertEqual(response.status_code, 404)

    def test_delete_review_twice_returns_404(self):
        _, created = create_review(self.client, self.reviewer["id"], self.place["id"])
        first = self.client.delete(f"/api/v1/reviews/{created['id']}")
        second = self.client.delete(f"/api/v1/reviews/{created['id']}")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 404)

    # ---------- GET /api/v1/places/<place_id>/reviews ----------

    def test_get_reviews_by_place(self):
        create_review(self.client, self.reviewer["id"], self.place["id"])
        response = self.client.get(f"/api/v1/places/{self.place['id']}/reviews")
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(len(body), 1)


if __name__ == "__main__":
    unittest.main()
