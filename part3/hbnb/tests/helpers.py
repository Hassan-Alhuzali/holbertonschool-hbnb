"""Shared helpers for the HBnB API test suite.

The application wires a single module-level ``HBnBFacade`` instance
(``app.services.facade``) backed by plain in-memory dictionaries, and
`create_app()` does not reset it. That means every test in the suite
shares the same storage and there is no endpoint to delete users, places,
or amenities. To keep tests independent of each other (and of execution
order), every helper here generates unique attribute values (emails,
names, titles) instead of relying on fixed fixtures.

Admin bootstrap
---------------
Since POST /api/v1/users/ is admin-only, test setup cannot create users
through the public API.  Use ``create_user_direct`` or
``create_user_and_login`` (which accepts the Flask ``app`` instance and
creates the user directly via the facade) for test infrastructure, and
``create_user`` (API call) only when testing the endpoint itself.
"""

import uuid


def unique_suffix():
    """Return a short unique string usable in emails/names/titles."""
    return uuid.uuid4().hex[:10]


def unique_email():
    return f"user.{unique_suffix()}@example.com"


# ---------------------------------------------------------------------------
# Low-level facade helpers (bypass the API – useful for test setup)
# ---------------------------------------------------------------------------

def create_user_direct(app, first_name="Test", last_name="User", email=None,
                       password="TestPass1!", is_admin=False):
    """Create a user directly via the facade, bypassing the JWT-protected API.

    Returns ``({'id': ...}, email)`` so callers can log in afterwards.
    """
    from app.services import facade
    email = email or unique_email()
    user = facade.create_user({
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password': password,
        'is_admin': is_admin,
    })
    return {'id': user.id}, email


def create_amenity_direct(app, name=None):
    """Create an amenity directly via the facade, bypassing the JWT-protected API.

    Returns ``{'id': ..., 'name': ...}``.
    """
    from app.services import facade
    name = name or f"Amenity-{unique_suffix()}"
    amenity = facade.create_amenity({'name': name})
    return {'id': amenity.id, 'name': amenity.name}


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def login_user(client, email, password="TestPass1!"):
    """Log in with the given credentials and return the JWT access token."""
    response = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password,
    })
    return response.get_json().get("access_token")


# ---------------------------------------------------------------------------
# Combined helpers
# ---------------------------------------------------------------------------

def create_user_and_login(client, app, first_name="Test", last_name="User",
                          password="TestPass1!"):
    """Create a regular user via the facade, log them in, and return (user_dict, token).

    The returned ``user_dict`` contains ``'id'`` and ``'email'``.
    """
    user_dict, email = create_user_direct(app, first_name=first_name,
                                          last_name=last_name, password=password)
    token = login_user(client, email, password)
    user_dict['email'] = email
    return user_dict, token


def create_admin_and_login(client, app, password="AdminPass1!"):
    """Create an admin user via the facade, log them in, and return (admin_dict, token).

    The returned ``admin_dict`` contains ``'id'`` and ``'email'``.
    """
    user_dict, email = create_user_direct(app, first_name="Admin", last_name="Admin",
                                           password=password, is_admin=True)
    token = login_user(client, email, password)
    user_dict['email'] = email
    return user_dict, token


# ---------------------------------------------------------------------------
# API-level helpers (require appropriate tokens)
# ---------------------------------------------------------------------------

def create_user(client, first_name="Test", last_name="User", email=None,
                password="TestPass1!", admin_token=None):
    """Create a user via the API (POST /api/v1/users/).

    Since this endpoint is admin-only, ``admin_token`` must be provided for a
    successful 201 response.  Omit it to test the 401/403 error paths.
    """
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email or unique_email(),
        "password": password,
    }
    headers = {}
    if admin_token:
        headers["Authorization"] = f"Bearer {admin_token}"
    response = client.post("/api/v1/users/", json=payload, headers=headers)
    return response, response.get_json()


def create_amenity(client, admin_token, name=None):
    """Create an amenity via the API (POST /api/v1/amenities/).

    Requires an admin JWT token.
    """
    payload = {"name": name or f"Amenity-{unique_suffix()}"}
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.post("/api/v1/amenities/", json=payload, headers=headers)
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
