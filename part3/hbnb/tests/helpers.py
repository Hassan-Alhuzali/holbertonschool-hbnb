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


def create_user(client, first_name="Test", last_name="User", email=None,
                password="TestPass1!"):
    """Create a user via the API and return (response, json_body)."""
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email or unique_email(),
        "password": password,
    }
    response = client.post("/api/v1/users/", json=payload)
    return response, response.get_json()


def login_user(client, email, password="TestPass1!"):
    """Log in with the given credentials and return the JWT access token."""
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    return response.get_json().get("access_token")


def create_user_and_login(client, first_name="Test", last_name="User",
                          password="TestPass1!"):
    """Create a user, log them in, and return (user_dict, token).

    The returned ``user_dict`` includes an ``'email'`` key so callers can
    log in again if needed (the POST response body does not include email).
    """
    email = unique_email()
    _, user = create_user(client, first_name=first_name, last_name=last_name,
                          email=email, password=password)
    token = login_user(client, email, password)
    user['email'] = email
    return user, token


def create_amenity(client, name=None):
    payload = {"name": name or f"Amenity-{unique_suffix()}"}
    response = client.post("/api/v1/amenities/", json=payload)
    return response, response.get_json()


def create_place(client, token, title=None, price=100.0, latitude=10.0,
                 longitude=10.0, description="A place to stay", amenities=None):
    """Create a place via the API using *token* for authentication.

    The owner is determined by the JWT identity encoded in *token*; no
    ``owner_id`` field is sent in the request body.
    """
    payload = {
        "title": title or f"Place-{unique_suffix()}",
        "description": description,
        "price": price,
        "latitude": latitude,
        "longitude": longitude,
    }
    if amenities is not None:
        payload["amenities"] = amenities
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/places/", json=payload, headers=headers)
    return response, response.get_json()


def create_review(client, place_id, token, text="Great stay!", rating=5):
    """Create a review via the API using *token* for authentication.

    The reviewer is determined by the JWT identity encoded in *token*; no
    ``user_id`` field is sent in the request body.
    """
    payload = {
        "text": text,
        "rating": rating,
        "place_id": place_id,
    }
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/reviews/", json=payload, headers=headers)
    return response, response.get_json()
