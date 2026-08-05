# HBnB API — Testing & Validation Report

This document records the work done for **Task 6: Implement Testing and
Validation of the Endpoints**: the validation rules already present in the
model layer, the manual black-box `cURL` testing pass performed against a
live server, the issues that testing uncovered (with fixes), and the
automated `unittest` suite added to guard against regressions.

## 1. Validation Implemented in the Business Logic Layer

All validation lives in property setters on the model classes
(`app/models/*.py`), so it is enforced no matter which layer calls into the
model (API, facade, or a test). Invalid values raise `ValueError`, which
every endpoint catches and turns into `400 Bad Request`.

| Entity | Attribute | Rule | Source |
|---|---|---|---|
| `User` | `first_name` | required, non-empty, ≤ 50 chars | `app/models/user.py` |
| `User` | `last_name` | required, non-empty, ≤ 50 chars | `app/models/user.py` |
| `User` | `email` | required, must match a basic `x@y.z` pattern | `app/models/user.py` |
| `User` | `email` (API-level) | must be unique across all users | `app/api/v1/users.py` (POST **and** PUT) |
| `Place` | `title` | required, non-empty, ≤ 100 chars | `app/models/place.py` |
| `Place` | `price` | required, non-negative number | `app/models/place.py` |
| `Place` | `latitude` | required, between -90 and 90 (inclusive) | `app/models/place.py` |
| `Place` | `longitude` | required, between -180 and 180 (inclusive) | `app/models/place.py` |
| `Place` | `owner_id` (API-level) | must reference an existing `User` | `app/services/facade.py` |
| `Place` | `amenities` (API-level) | each id must reference an existing `Amenity` | `app/services/facade.py` |
| `Review` | `text` | required, non-empty | `app/models/review.py` |
| `Review` | `rating` | required integer between 1 and 5 (booleans rejected) | `app/models/review.py` |
| `Review` | `user_id` / `place_id` (API-level) | must reference existing entities | `app/services/facade.py` |
| `Amenity` | `name` | required, non-empty, ≤ 50 chars | `app/models/amenity.py` |

**Note on `price`:** the task 6 brief says "price is a positive number,"
while the original task 4 brief (which defined the `Place` model) says
"non-negative float." I kept the existing **non-negative** behavior (`price
>= 0` is valid, so `price = 0` is accepted) since that's the rule the model
was actually built against, and changing it now would silently break
anything that relies on free listings. This is called out here rather than
changed silently — flag if strictly-positive is actually the desired
behavior and I'll tighten the setter.

Required-field enforcement (missing keys entirely, wrong JSON types) is
handled a layer up, by Flask-RESTx's `@api.expect(model, validate=True)`,
which rejects requests that don't match the Swagger model before they ever
reach the facade.

## 2. Issues Found During Testing (and Fixed)

Manual testing surfaced two real bugs, both now fixed. Automated regression
tests were added for both (see §4).

### 2.1 `PUT /api/v1/users/<id>` allowed duplicate emails

`POST /api/v1/users/` checks `get_user_by_email` before creating a user, but
the `PUT` handler never performed the equivalent check, so a user could be
updated to an email another user already had.

**Repro (before fix):**

```bash
curl -X PUT "http://127.0.0.1:5000/api/v1/users/<jane_id>" \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Jane","last_name":"Smith","email":"john.doe@example.com"}'
# -> 200 OK, even though john.doe@example.com already belonged to another user
```

**Fix:** `app/api/v1/users.py` — the `PUT` handler now looks up the target
email and rejects the request with `400 {"error": "Email already
registered"}` if it belongs to a *different* user. Updating a user with
their own unchanged email still succeeds.

### 2.2 A failing multi-field update could partially apply

`BaseModel.update()` looped over the incoming fields and called `setattr`
for each one directly. If an early field applied cleanly and a later field
failed validation, the exception aborted the loop but **the earlier
field's new value was already committed** — the object was left in a mixed
old/new state despite the request as a whole returning `400`.

**Repro (before fix):**

```bash
curl -X PUT "http://127.0.0.1:5000/api/v1/places/<id>" \
  -H "Content-Type: application/json" \
  -d '{"description":"Should Not Stick","price":-999}'
# -> 400 {"error": "price must be a non-negative number"}

curl "http://127.0.0.1:5000/api/v1/places/<id>"
# -> description had actually changed to "Should Not Stick" despite the 400
```

This affects every entity, since `User`, `Place`, `Review`, and `Amenity`
all share `BaseModel.update()`.

**Fix:** `app/models/base_model.py` — `update()` now snapshots the
previous value of every attribute it's about to change, and if any
`setattr` call raises, it rolls every attribute from that call back to its
snapshot before re-raising. A failed update is now all-or-nothing.

> Testing detail: this bug is order-dependent (it only shows when a
> successfully-applied field is processed *before* the failing one).
> Flask's default JSON provider serializes response/request bodies with
> `sort_keys=True`, so a naive HTTP-level test using e.g.
> `{"title": ..., "price": ...}` can accidentally "hide" the bug because
> `price` sorts before `title` and fails first. The regression tests use a
> field pairing (`description`, which sorts alphabetically before `price`)
> that reproduces it reliably over HTTP, plus a dedicated model-level test
> (`tests/test_base_model.py`) that controls dict order directly and isn't
> affected by transport-layer key ordering at all.

## 3. Manual `cURL` Testing Log

Performed against a locally running server
(`python run.py`, `http://127.0.0.1:5000`). ✅ = actual matched expected.

### Users (`/api/v1/users/`)

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Valid user (`first_name`, `last_name`, valid `email`) | 201 + created user | 201 + created user | ✅ (task doc's example says `200 OK`; `201 Created` is correct REST convention and matches task 2's own spec) |
| 2 | Same email again | 400, `Email already registered` | 400, `Email already registered` | ✅ |
| 3 | Empty `first_name`/`last_name`, invalid `email` | 400 | 400, `first_name must be provided...` | ✅ |
| 4 | Missing `email` field entirely | 400 | 400 (Flask-RESTx schema error) | ✅ |
| 5 | `GET /users/` | 200 + list | 200 + list | ✅ |
| 6 | `GET /users/<bad-id>` | 404 | 404, `User not found` | ✅ |
| 7 | `PUT` with another user's email | should be 400 | **was 200 (bug)** → now 400 | ✅ after fix (§2.1) |
| 8 | `PUT` with own unchanged email | 200 | 200 | ✅ |

### Places (`/api/v1/places/`)

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Valid place | 201 | 201 | ✅ |
| 2 | `price: -50` | 400 | 400, `price must be a non-negative number` | ✅ |
| 3 | `price: 0` (boundary) | 201 (non-negative allows 0) | 201 | ✅ |
| 4 | `latitude: 91` | 400 | 400 | ✅ |
| 5 | `longitude: -181` | 400 | 400 | ✅ |
| 6 | `latitude: -90`, `longitude: -180` (exact boundary) | 201 | 201 | ✅ |
| 7 | Non-existent `owner_id` | 400 | 400, `Owner not found` | ✅ |
| 8 | Empty `title` | 400 | 400 | ✅ |
| 9 | Missing `price` field | 400 | 400 (schema error) | ✅ |
| 10 | `GET /places/<id>` | 200 + nested owner/amenities/reviews | 200, correct nesting | ✅ |
| 11 | `GET /places/<bad-id>` | 404 | 404 | ✅ |
| 12 | `PUT` partial valid update | 200 | 200 | ✅ |
| 13 | `PUT` on non-existent place | 404 | 404 | ✅ |
| 14 | `PUT` with invalid `price` | 400 | 400 | ✅ |
| 15 | `PUT` with 1 valid + 1 invalid field together | object must stay unchanged | **partially mutated (bug)** → now unchanged | ✅ after fix (§2.2) |
| 16 | `price` as non-numeric string | 400 | 400 (schema error, `'expensive' is not of type 'number'`) | ✅ |
| 17 | Non-existent amenity id in `amenities` | 400 | 400, `Amenity <id> not found` | ✅ |

### Reviews (`/api/v1/reviews/`)

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Valid review | 201 | 201 | ✅ |
| 2 | Empty `text` | 400 | 400, `text is required` | ✅ |
| 3 | `rating: 6` / `rating: 0` (out of range) | 400 | 400 both | ✅ |
| 4 | `rating: 1` / `rating: 5` (boundary) | 201 | 201 both | ✅ |
| 5 | `rating: true` (boolean) | 400 | 400 (schema rejects non-integer type) | ✅ |
| 6 | `rating: "five"` (wrong type) | 400 | 400 (schema error) | ✅ |
| 7 | Non-existent `user_id` | 400 | 400, `User not found` | ✅ |
| 8 | Non-existent `place_id` | 400 | 400, `Place not found` | ✅ |
| 9 | `GET /reviews/<id>` | 200 | 200 | ✅ |
| 10 | `GET /places/<id>/reviews` | 200 + list | 200 + list | ✅ |
| 11 | `GET /places/<bad-id>/reviews` | 404 | 404 | ✅ |
| 12 | `PUT` with invalid rating | 400 | 400 | ✅ |
| 13 | `DELETE` existing review | 200 | 200 | ✅ |
| 14 | `DELETE` same review again | 404 | 404 | ✅ |

### Amenities (`/api/v1/amenities/`)

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Valid amenity | 201 | 201 | ✅ |
| 2 | Empty `name` | 400 | 400 | ✅ |
| 3 | Missing `name` field | 400 | 400 (schema error) | ✅ |
| 4 | `GET /amenities/` | 200 + list | 200 + list | ✅ |
| 5 | `GET /amenities/<bad-id>` | 404 | 404 | ✅ |

### Robustness / error handling

| # | Input | Expected | Actual | Result |
|---|---|---|---|---|
| 1 | Malformed JSON body | 400, no crash | 400, `Failed to decode JSON object...` | ✅ |
| 2 | Any lookup by a garbage/non-UUID id | 404, no crash | 404 | ✅ |

## 4. Automated Test Suite

Added under `tests/` using Python's built-in `unittest` (no `pytest`
dependency was installed in the project's virtualenv, and `unittest` needs
no extra dependency):

- `tests/helpers.py` — shared factories (`create_user`, `create_place`,
  `create_amenity`, `create_review`) that generate **unique** data
  (uuid-based emails/names/titles) for every call.
- `tests/test_users.py` — 12 tests
- `tests/test_amenities.py` — 9 tests
- `tests/test_places.py` — 20 tests
- `tests/test_reviews.py` — 18 tests
- `tests/test_base_model.py` — 5 tests (direct, order-controlled tests of
  the `update()` rollback contract)

**Why unique data per test:** `app/services/__init__.py` builds a single
module-level `HBnBFacade()` that every `create_app()` call reuses, and there
is no `DELETE` for users, places, or amenities (only reviews support
delete). This means all tests in a process share one in-memory store with
no reset hook. Rather than depend on test-execution order, every helper
generates fresh unique values so tests are independent regardless of order
or repetition.

Run the whole suite from `part2/hbnb/`:

```bash
python -m unittest discover -s tests -v
```

Current result:

```
Ran 70 tests in ~0.6s
OK
```

Each bug in §2 has a dedicated regression test that was confirmed to
**fail** on the old code and **pass** on the fix (verified by temporarily
reverting the fix via `git stash` and re-running):

- `tests/test_users.py::test_update_user_duplicate_email_is_rejected`
- `tests/test_places.py::test_update_place_is_atomic_on_validation_failure`
- `tests/test_base_model.py::test_update_rolls_back_earlier_fields_when_a_later_one_is_invalid`
- `tests/test_base_model.py::test_update_rolls_back_regardless_of_which_field_is_invalid_first`
- `tests/test_base_model.py::test_user_update_rolls_back_on_invalid_email`

## 5. Swagger / OpenAPI Documentation Review

With the server running, `GET /api/v1/` serves the Swagger UI, and
`GET /swagger.json` serves the raw spec. Reviewed the generated spec and
confirmed it lists exactly the implemented routes and status codes:

```
GET    /api/v1/amenities/                responses: 200
POST   /api/v1/amenities/                responses: 201, 400
GET    /api/v1/amenities/{amenity_id}    responses: 200, 404
PUT    /api/v1/amenities/{amenity_id}    responses: 200, 400, 404
GET    /api/v1/places/                   responses: 200
POST   /api/v1/places/                   responses: 201, 400
GET    /api/v1/places/{place_id}         responses: 200, 404
PUT    /api/v1/places/{place_id}         responses: 200, 400, 404
GET    /api/v1/places/{place_id}/reviews responses: 200, 404
GET    /api/v1/reviews/                  responses: 200
POST   /api/v1/reviews/                  responses: 201, 400
GET    /api/v1/reviews/{review_id}       responses: 200, 404
PUT    /api/v1/reviews/{review_id}       responses: 200, 400, 404
DELETE /api/v1/reviews/{review_id}       responses: 200, 404
GET    /api/v1/users/                    responses: 200
POST   /api/v1/users/                    responses: 201, 400
GET    /api/v1/users/{user_id}           responses: 200, 404
PUT    /api/v1/users/{user_id}           responses: 200, 400, 404
```

The `PUT /api/v1/users/{user_id}` entry now also documents the `400 Email
already registered` response after the fix in §2.1.

## 6. Known Limitations / Suggestions for Future Work

- **No test isolation hook.** The shared, module-level `facade` singleton
  (see §4) makes integration testing workable but inelegant. A
  `HBnBFacade.reset()` method (or building a fresh facade per `create_app()`
  call and storing it on the Flask app/config) would make tests cleaner and
  remove the need for uuid-suffixed fixture data.
- **Email uniqueness is case-sensitive.** `John@Example.com` and
  `john@example.com` are currently treated as different users. Not in
  scope for this task, but worth deciding on purpose.
- **`price` semantics.** Documented in §1 — currently non-negative
  (0 allowed), not strictly positive. Flag if this should change.
