"""Shared helpers for the HBnB API test suite.

The application wires a single module-level ``HBnBFacade`` instance
(``app.services.facade``) backed by plain in-memory dictionaries, and
`create_app()` does not reset it. That means every test in the suite
shares the same storage and there is no endpoint to delete users, places,
or amenities. To keep tests independent of each other (and of execution
order), every helper here generates unique attribute values (emails,
names, titles) instead of relying on fixed fixtures.
"""

import uuid


def unique_suffix():
    """Return a short unique string usable in emails/names/titles."""
    return uuid.uuid4().hex[:10]


def unique_email():
    return f"user.{unique_suffix()}@example.com"


def create_user(client, first_name="Test", last_name="User", email=None):
    """Create a user via the API and return (response, json_body)."""
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email or unique_email(),
    }
    response = client.post("/api/v1/users/", json=payload)
    return response, response.get_json()


def create_amenity(client, name=None):
    payload = {"name": name or f"Amenity-{unique_suffix()}"}
    response = client.post("/api/v1/amenities/", json=payload)
    return response, response.get_json()


def create_place(client, owner_id, title=None, price=100.0, latitude=10.0,
                  longitude=10.0, description="A place to stay", amenities=None):
    payload = {
        "title": title or f"Place-{unique_suffix()}",
        "description": description,
        "price": price,
        "latitude": latitude,
        "longitude": longitude,
        "owner_id": owner_id,
    }
    if amenities is not None:
        payload["amenities"] = amenities
    response = client.post("/api/v1/places/", json=payload)
    return response, response.get_json()


def create_review(client, user_id, place_id, text="Great stay!", rating=5):
    payload = {
        "text": text,
        "rating": rating,
        "user_id": user_id,
        "place_id": place_id,
    }
    response = client.post("/api/v1/reviews/", json=payload)
    return response, response.get_json()
