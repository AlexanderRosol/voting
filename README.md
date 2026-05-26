# Voting Application

REST API for a voting application: users, polls, poll options, votes, and results. The data model lives in `schema.sql` and the API contract in `app/openapi.yaml`. This README covers how to configure, run, and test the implementation.

## Architecture

- **Flask** application factory in `app/app.py` (`create_app()`).
- **SQLAlchemy 2.0** models in `app/models.py` (entities: `User`, `Poll`, `PollOption`, `Vote`).
- **Flask-JWT-Extended** for token-based authentication. `POST /auth/token` issues a JWT; protected endpoints require `Authorization: Bearer <token>`.
- **Blueprints**, one per resource group, in `app/views/`: `auth.py`, `users.py`, `polls.py`, `votes.py`.
- **Flasgger** serves the OpenAPI spec at `/apidocs` for live demos.
- **Config** in `app/config.py`. Tests inject overrides through `create_app(test_config=...)`.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ (production / demo runs)
- A virtual environment is recommended

## Configure

The default database URL is set in `app/config.py`:

```
postgresql+psycopg2:///voting
```

This connects to the local PostgreSQL instance as the current OS user (peer/socket auth) against a database named `voting`. Create the database once:

```bash
createdb voting
```

If you prefer to use a dedicated role with a password, edit `SQLALCHEMY_DATABASE_URI` in `app/config.py` to:

```
postgresql+psycopg2://<user>:<password>@localhost:5432/voting
```

and create the role with `createuser <user> -P`.

JWT signing key (`JWT_SECRET_KEY`) is also in `app/config.py`. The default `dev-jwt-secret` is for local lab use only.

## Install

```bash
cd voting
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python run.py
```

The server binds to `http://127.0.0.1:5000`. Schema tables are created automatically on first boot via `db.create_all()`.

## Swagger UI (for demo)

Open `http://127.0.0.1:5000/apidocs` in a browser. Flasgger renders `app/openapi.yaml` and lets you exercise every endpoint. For protected routes click **Authorize** and paste `Bearer <token>` after obtaining one via `POST /auth/token`.

## Authentication flow

1. **Create a user** — `POST /users` with `{"username", "email", "password"}`. Returns the user JSON (without the password).
2. **Get a token** — `POST /auth/token` with `{"username", "password"}`. Returns `{"access_token", "token_type": "bearer"}`.
3. **Call protected endpoints** — include the header `Authorization: Bearer <access_token>`.

Example session:

```bash
curl -sS -X POST http://127.0.0.1:5000/users \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"alicepw1"}'

TOKEN=$(curl -sS -X POST http://127.0.0.1:5000/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"alicepw1"}' | jq -r .access_token)

curl -sS http://127.0.0.1:5000/users -H "Authorization: Bearer $TOKEN"
```

## Tests

```bash
cd voting
pytest -q
```

Tests run against an in-memory SQLite database via the `test_config` override in `tests/conftest.py`, so PostgreSQL does not need to be running. Each implemented endpoint has at least one unit test covering both success and error paths.

## Endpoint summary

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/token` | public | Exchange username + password for a JWT |
| GET | `/users` | bearer | List voters |
| POST | `/users` | public | Create a new user |
| GET | `/users/{userId}` | bearer | Get a specific user |
| PUT | `/users/{userId}` | bearer (self) | Update a user |
| DELETE | `/users/{userId}` | bearer (self) | Delete a user |
| GET | `/polls` | public | List all polls |
| POST | `/polls` | bearer | Create a poll |
| GET | `/polls/{pollId}` | public | Get a poll |
| PATCH | `/polls/{pollId}` | bearer (owner) | Update a poll |
| DELETE | `/polls/{pollId}` | bearer (owner) | Delete a poll |
| GET | `/polls/{pollId}/options` | public | List a poll's options |
| POST | `/polls/{pollId}/options` | bearer (owner) | Add an option |
| GET | `/polls/{pollId}/votes` | bearer | List votes for a poll |
| POST | `/polls/{pollId}/votes` | bearer | Cast a vote (409 on duplicate) |
| GET | `/polls/{pollId}/results` | public | Tallied results |
| GET | `/votes/{voteId}` | bearer | Get a single vote record |
| DELETE | `/votes/{voteId}` | bearer (owner) | Delete a vote |

## Status codes used

- `200 OK` — success with body
- `201 Created` — resource created
- `204 No Content` — successful delete
- `400 Bad Request` — invalid input / malformed JSON / missing fields
- `401 Unauthorized` — missing or invalid JWT
- `403 Forbidden` — authenticated but not the resource owner
- `404 Not Found` — resource missing
- `409 Conflict` — duplicate vote (`UNIQUE(user_id, poll_id)`)

Error bodies follow the `ErrorResponse` schema from `openapi.yaml`:

```json
{ "code": 400, "message": "..." }
```

## Spec deviations

`openapi.yaml`'s `UserInput` schema lists only `username` and `email`, but `schema.sql` declares `password NOT NULL`. The implementation accepts an additional `password` field on `POST /users` so newly created users can authenticate via `POST /auth/token`. This is the only deviation from `openapi.yaml`.
