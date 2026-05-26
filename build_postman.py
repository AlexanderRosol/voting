"""Build voting_api.postman_collection.json focused on the two graded criteria:
   - Endpoints protected against improperly formatted input data (2 pts)
   - 2xx + error responses for randomly-selected endpoints (6 x 2 pts)

Every one of the 18 endpoints from openapi.yaml has both a 2xx example and at
least one error example. Endpoints with a request body have an input-validation
(400) error to demonstrate input protection."""

import json
from pathlib import Path

BASE = "{{baseUrl}}"


def url(path):
    return {
        "raw": BASE + path,
        "host": [BASE],
        "path": [p for p in path.lstrip("/").split("/") if p],
    }


def request(method, path, *, body=None, token=None):
    headers = []
    if body is not None:
        headers.append({"key": "Content-Type", "value": "application/json"})
    if token:
        headers.append({"key": "Authorization", "value": f"Bearer {{{{{token}}}}}"})
    req = {"method": method, "header": headers, "url": url(path)}
    if body is not None:
        raw = body if isinstance(body, str) else json.dumps(body, indent=2)
        req["body"] = {
            "mode": "raw",
            "raw": raw,
            "options": {"raw": {"language": "json"}},
        }
    return req


def test_event(lines):
    return {
        "listen": "test",
        "script": {"type": "text/javascript", "exec": lines},
    }


def item(name, req, test_lines):
    return {
        "name": name,
        "event": [test_event(test_lines)],
        "request": req,
        "response": [],
    }


def status_test(code, extra=None):
    lines = [
        f"pm.test('Status {code}', function () {{",
        f"    pm.response.to.have.status({code});",
        "});",
    ]
    if extra:
        lines += extra
    return lines


def error_shape_test():
    return [
        "pm.test('Error has code and message', function () {",
        "    const body = pm.response.json();",
        "    pm.expect(body).to.have.property('code');",
        "    pm.expect(body).to.have.property('message');",
        "});",
    ]


# ----------------------------------------------------------------------
# Setup folder — creates Alice, Bob, tokens, poll, option, vote so every
# downstream request has the IDs it needs.
# ----------------------------------------------------------------------

setup = [
    item(
        "Create user Alice  (201)",
        request("POST", "/users", body=(
            '{\n'
            '  "username": "alice_{{run_suffix}}",\n'
            '  "email": "alice_{{run_suffix}}@example.com",\n'
            '  "password": "alicepw1"\n'
            '}'
        )),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('user_a_id', body.id);",
            "pm.collectionVariables.set('username_a', body.username);",
        ]),
    ),
    item(
        "Login Alice  (200)",
        request("POST", "/auth/token", body=(
            '{\n'
            '  "username": "{{username_a}}",\n'
            '  "password": "alicepw1"\n'
            '}'
        )),
        status_test(200, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('token_a', body.access_token);",
        ]),
    ),
    item(
        "Create user Bob  (201)",
        request("POST", "/users", body=(
            '{\n'
            '  "username": "bob_{{run_suffix}}",\n'
            '  "email": "bob_{{run_suffix}}@example.com",\n'
            '  "password": "bobpw12345"\n'
            '}'
        )),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('user_b_id', body.id);",
            "pm.collectionVariables.set('username_b', body.username);",
        ]),
    ),
    item(
        "Login Bob  (200)",
        request("POST", "/auth/token", body=(
            '{\n'
            '  "username": "{{username_b}}",\n'
            '  "password": "bobpw12345"\n'
            '}'
        )),
        status_test(200, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('token_b', body.access_token);",
        ]),
    ),
    item(
        "Alice creates poll  (201)",
        request("POST", "/polls", token="token_a", body={
            "title": "Favourite color",
            "description": "Pick one",
            "status": "active",
        }),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('poll_id', body.id);",
        ]),
    ),
    item(
        "Alice adds option 'red'  (201)",
        request("POST", "/polls/{{poll_id}}/options", token="token_a", body={
            "option_text": "red",
            "display_order": 1,
        }),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('option_id', body.id);",
        ]),
    ),
    item(
        "Alice adds option 'blue'  (201)",
        request("POST", "/polls/{{poll_id}}/options", token="token_a", body={
            "option_text": "blue",
            "display_order": 2,
        }),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('option_blue_id', body.id);",
        ]),
    ),
    item(
        "Alice casts vote  (201)",
        request("POST", "/polls/{{poll_id}}/votes", token="token_a", body={
            "option_id": "{{option_id}}",
        }),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('vote_a_id', body.id);",
        ]),
    ),
    item(
        "Bob casts vote  (201) — for /votes/{id} ownership tests later",
        request("POST", "/polls/{{poll_id}}/votes", token="token_b", body={
            "option_id": "{{option_blue_id}}",
        }),
        status_test(201, [
            "const body = pm.response.json();",
            "pm.collectionVariables.set('vote_b_id', body.id);",
        ]),
    ),
]

# ----------------------------------------------------------------------
# Per-endpoint folders.  Each folder shows the 2xx case plus one or more
# error cases.  Endpoints that accept a body always have a 400 case
# demonstrating input-format protection.
# ----------------------------------------------------------------------

auth = [
    item(
        "POST /auth/token  (200) — success",
        request("POST", "/auth/token", body=(
            '{\n'
            '  "username": "{{username_a}}",\n'
            '  "password": "alicepw1"\n'
            '}'
        )),
        status_test(200, [
            "pm.test('Has bearer token', function () {",
            "    const b = pm.response.json();",
            "    pm.expect(b.token_type).to.eql('bearer');",
            "    pm.expect(b.access_token).to.be.a('string');",
            "});",
        ]),
    ),
    item(
        "POST /auth/token  (400) — wrong password",
        request("POST", "/auth/token", body=(
            '{\n'
            '  "username": "{{username_a}}",\n'
            '  "password": "WRONG"\n'
            '}'
        )),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /auth/token  (400) — missing password (bad input)",
        request("POST", "/auth/token", body=(
            '{\n'
            '  "username": "{{username_a}}"\n'
            '}'
        )),
        status_test(400, error_shape_test()),
    ),
]

users = [
    item(
        "GET /users  (200) — list",
        request("GET", "/users", token="token_a"),
        status_test(200, [
            "pm.test('Is array', function () {",
            "    pm.expect(pm.response.json()).to.be.an('array');",
            "});",
        ]),
    ),
    item(
        "GET /users  (401) — no token",
        request("GET", "/users"),
        status_test(401, error_shape_test()),
    ),
    item(
        "POST /users  (201) — create",
        request("POST", "/users", body=(
            '{\n'
            '  "username": "carol_{{run_suffix}}",\n'
            '  "email": "carol_{{run_suffix}}@example.com",\n'
            '  "password": "carolpw1"\n'
            '}'
        )),
        status_test(201),
    ),
    item(
        "POST /users  (400) — bad email format (bad input)",
        request("POST", "/users", body={
            "username": "dave",
            "email": "not-an-email",
            "password": "davepw123",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /users  (400) — missing password (bad input)",
        request("POST", "/users", body={
            "username": "dave",
            "email": "dave@example.com",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /users  (400) — username too long >30 (bad input)",
        request("POST", "/users", body={
            "username": "x" * 31,
            "email": "x@example.com",
            "password": "xpassword",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "GET /users/{id}  (200)",
        request("GET", "/users/{{user_a_id}}", token="token_a"),
        status_test(200),
    ),
    item(
        "GET /users/{id}  (404) — random uuid",
        request("GET", "/users/00000000-0000-0000-0000-000000000000", token="token_a"),
        status_test(404, error_shape_test()),
    ),
    item(
        "PUT /users/{id}  (200) — Alice updates herself",
        request("PUT", "/users/{{user_a_id}}", token="token_a", body=(
            '{\n'
            '  "username": "{{username_a}}",\n'
            '  "email": "alice_{{run_suffix}}_updated@example.com"\n'
            '}'
        )),
        status_test(200),
    ),
    item(
        "PUT /users/{id}  (400) — bad email (bad input)",
        request("PUT", "/users/{{user_a_id}}", token="token_a", body={
            "username": "{{username_a}}",
            "email": "broken",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "PUT /users/{id}  (403) — Bob tries to update Alice",
        request("PUT", "/users/{{user_a_id}}", token="token_b", body={
            "username": "hijacked",
            "email": "hijacked@example.com",
        }),
        status_test(403, error_shape_test()),
    ),
    # DELETE /users/{id} is exercised in the Teardown folder so we still
    # have Alice/Bob for later requests.
    item(
        "DELETE /users/{id}  (403) — Bob tries to delete Alice",
        request("DELETE", "/users/{{user_a_id}}", token="token_b"),
        status_test(403, error_shape_test()),
    ),
]

polls = [
    item(
        "GET /polls  (200) — public list",
        request("GET", "/polls"),
        status_test(200),
    ),
    item(
        "POST /polls  (201)",
        request("POST", "/polls", token="token_a", body={
            "title": "Best food",
            "status": "draft",
        }),
        status_test(201),
    ),
    item(
        "POST /polls  (401) — no token",
        request("POST", "/polls", body={"title": "x"}),
        status_test(401, error_shape_test()),
    ),
    item(
        "POST /polls  (400) — missing title (bad input)",
        request("POST", "/polls", token="token_a", body={"description": "no title"}),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls  (400) — title too long >120 (bad input)",
        request("POST", "/polls", token="token_a", body={"title": "x" * 121}),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls  (400) — bad status enum (bad input)",
        request("POST", "/polls", token="token_a", body={
            "title": "x", "status": "not-a-status",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls  (400) — bad expires_at (bad input)",
        request("POST", "/polls", token="token_a", body={
            "title": "x", "expires_at": "not-a-date",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "GET /polls/{id}  (200)",
        request("GET", "/polls/{{poll_id}}"),
        status_test(200),
    ),
    item(
        "GET /polls/{id}  (404)",
        request("GET", "/polls/00000000-0000-0000-0000-000000000000"),
        status_test(404, error_shape_test()),
    ),
    item(
        "PATCH /polls/{id}  (200)",
        request("PATCH", "/polls/{{poll_id}}", token="token_a", body={
            "status": "closed",
        }),
        status_test(200),
    ),
    item(
        "PATCH /polls/{id}  (400) — bad status (bad input)",
        request("PATCH", "/polls/{{poll_id}}", token="token_a", body={
            "status": "garbage",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "PATCH /polls/{id}  (403) — Bob tries to edit Alice's poll",
        request("PATCH", "/polls/{{poll_id}}", token="token_b", body={
            "title": "stolen",
        }),
        status_test(403, error_shape_test()),
    ),
]

options = [
    item(
        "GET /polls/{id}/options  (200) — public list",
        request("GET", "/polls/{{poll_id}}/options"),
        status_test(200),
    ),
    item(
        "GET /polls/{id}/options  (404) — unknown poll",
        request("GET", "/polls/00000000-0000-0000-0000-000000000000/options"),
        status_test(404, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/options  (201)",
        request("POST", "/polls/{{poll_id}}/options", token="token_a", body={
            "option_text": "green", "display_order": 3,
        }),
        status_test(201),
    ),
    item(
        "POST /polls/{id}/options  (400) — text too long >100 (bad input)",
        request("POST", "/polls/{{poll_id}}/options", token="token_a", body={
            "option_text": "x" * 101,
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/options  (400) — non-int display_order (bad input)",
        request("POST", "/polls/{{poll_id}}/options", token="token_a", body={
            "option_text": "yellow", "display_order": "first",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/options  (403) — Bob tries on Alice's poll",
        request("POST", "/polls/{{poll_id}}/options", token="token_b", body={
            "option_text": "magenta",
        }),
        status_test(403, error_shape_test()),
    ),
]

poll_votes = [
    item(
        "GET /polls/{id}/votes  (200)",
        request("GET", "/polls/{{poll_id}}/votes", token="token_a"),
        status_test(200),
    ),
    item(
        "GET /polls/{id}/votes  (401) — no token",
        request("GET", "/polls/{{poll_id}}/votes"),
        status_test(401, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/votes  (409) — Alice already voted in setup",
        request("POST", "/polls/{{poll_id}}/votes", token="token_a", body={
            "option_id": "{{option_id}}",
        }),
        status_test(409, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/votes  (400) — option_id not a UUID (bad input)",
        request("POST", "/polls/{{poll_id}}/votes", token="token_a", body={
            "option_id": "not-a-uuid",
        }),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/votes  (400) — missing option_id (bad input)",
        request("POST", "/polls/{{poll_id}}/votes", token="token_a", body={}),
        status_test(400, error_shape_test()),
    ),
    item(
        "POST /polls/{id}/votes  (404) — option doesn't belong to poll",
        request("POST", "/polls/{{poll_id}}/votes", token="token_a", body={
            "option_id": "00000000-0000-0000-0000-000000000000",
        }),
        status_test(404, error_shape_test()),
    ),
]

results = [
    item(
        "GET /polls/{id}/results  (200) — tallied",
        request("GET", "/polls/{{poll_id}}/results"),
        status_test(200, [
            "pm.test('Has poll and options', function () {",
            "    const b = pm.response.json();",
            "    pm.expect(b).to.have.property('poll');",
            "    pm.expect(b.options).to.be.an('array');",
            "});",
        ]),
    ),
    item(
        "GET /polls/{id}/results  (404)",
        request("GET", "/polls/00000000-0000-0000-0000-000000000000/results"),
        status_test(404, error_shape_test()),
    ),
]

vote_records = [
    item(
        "GET /votes/{id}  (200)",
        request("GET", "/votes/{{vote_a_id}}", token="token_a"),
        status_test(200),
    ),
    item(
        "GET /votes/{id}  (401) — no token",
        request("GET", "/votes/{{vote_a_id}}"),
        status_test(401, error_shape_test()),
    ),
    item(
        "GET /votes/{id}  (404)",
        request("GET", "/votes/00000000-0000-0000-0000-000000000000", token="token_a"),
        status_test(404, error_shape_test()),
    ),
    item(
        "DELETE /votes/{id}  (403) — Bob tries to delete Alice's vote",
        request("DELETE", "/votes/{{vote_a_id}}", token="token_b"),
        status_test(403, error_shape_test()),
    ),
    item(
        "DELETE /votes/{id}  (204) — Bob deletes his own vote",
        request("DELETE", "/votes/{{vote_b_id}}", token="token_b"),
        status_test(204),
    ),
    item(
        "DELETE /votes/{id}  (404)",
        request("DELETE", "/votes/00000000-0000-0000-0000-000000000000", token="token_a"),
        status_test(404, error_shape_test()),
    ),
]

teardown = [
    item(
        "DELETE /polls/{id}  (403) — Bob tries to delete Alice's poll",
        request("DELETE", "/polls/{{poll_id}}", token="token_b"),
        status_test(403, error_shape_test()),
    ),
    item(
        "DELETE /polls/{id}  (204) — Alice deletes her own poll",
        request("DELETE", "/polls/{{poll_id}}", token="token_a"),
        status_test(204),
    ),
    item(
        "DELETE /users/{id}  (204) — Alice deletes herself",
        request("DELETE", "/users/{{user_a_id}}", token="token_a"),
        status_test(204),
    ),
    item(
        "DELETE /users/{id}  (204) — Bob deletes himself",
        request("DELETE", "/users/{{user_b_id}}", token="token_b"),
        status_test(204),
    ),
]


# ----------------------------------------------------------------------

collection = {
    "info": {
        "name": "Voting API",
        "description": (
            "Demonstrates every endpoint defined in app/openapi.yaml with a 2xx "
            "happy path plus at least one error case.  Endpoints that accept a "
            "JSON body have a 400 case showing input-format protection.\n\n"
            "Run the requests in order (Collection Runner does this automatically) "
            "after starting the server with `python run.py`.  "
            "Each run uses a fresh `run_suffix` so it can be replayed against the "
            "same database."
        ),
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "event": [
        {
            "listen": "prerequest",
            "script": {
                "type": "text/javascript",
                "exec": [
                    "// Generate a per-run suffix so user/email values stay unique",
                    "if (!pm.collectionVariables.get('run_suffix')) {",
                    "    pm.collectionVariables.set('run_suffix', Date.now().toString());",
                    "}",
                ],
            },
        }
    ],
    "variable": [
        {"key": "baseUrl", "value": "http://127.0.0.1:5000"},
        {"key": "run_suffix", "value": ""},
        {"key": "token_a", "value": ""},
        {"key": "token_b", "value": ""},
        {"key": "username_a", "value": ""},
        {"key": "username_b", "value": ""},
        {"key": "user_a_id", "value": ""},
        {"key": "user_b_id", "value": ""},
        {"key": "poll_id", "value": ""},
        {"key": "option_id", "value": ""},
        {"key": "option_blue_id", "value": ""},
        {"key": "vote_a_id", "value": ""},
        {"key": "vote_b_id", "value": ""},
    ],
    "item": [
        {"name": "00 - Setup",                 "item": setup},
        {"name": "01 - POST /auth/token",       "item": auth},
        {"name": "02 - /users",                 "item": users},
        {"name": "03 - /polls",                 "item": polls},
        {"name": "04 - /polls/{id}/options",    "item": options},
        {"name": "05 - /polls/{id}/votes",      "item": poll_votes},
        {"name": "06 - /polls/{id}/results",    "item": results},
        {"name": "07 - /votes/{id}",            "item": vote_records},
        {"name": "99 - Teardown",               "item": teardown},
    ],
}

out = Path(__file__).parent / "voting_api.postman_collection.json"
out.write_text(json.dumps(collection, indent=2))
print(f"Wrote {out}  ({sum(len(f['item']) for f in collection['item']) } requests)")
