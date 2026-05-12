# Voting Application

## Overview

This repository contains a simple voting application data model and OpenAPI specification.

- `schema.sql` — PostgreSQL schema for users, polls, poll options, and votes.
- `openapi.yaml` — OpenAPI 3.1 specification for the REST API.

## What the application models

- `users` — voters
- `polls` — voting topics
- `poll_options` — choices belonging to a poll
- `votes` — a user vote for a specific option in a poll

## Assignment coverage

### Database requirements

- Real database software model: `schema.sql` is written for PostgreSQL.
- At least 3 tables: yes (`users`, `polls`, `poll_options`, `votes`).
- At least 1 relationship: yes, foreign keys relate:
  - `polls.created_by -> users.id`
  - `poll_options.poll_id -> polls.id`
  - `votes.user_id -> users.id`
  - `votes.poll_id -> polls.id`
  - `votes.option_id -> poll_options.id`
- At least 10 columns total: yes (more than 10 columns across all tables).

### API specification requirements

- REST-compliant structure: paths use nouns and are logically organized.
- Relationship-based paths: yes, e.g. `/polls/{pollId}/options` and `/polls/{pollId}/votes`.
- At least 9 endpoints: yes, including user, poll, option, vote, and result endpoints.
- Each HTTP method present: GET, POST, PUT, DELETE are all included.
- JSON structured data: yes, responses are defined in JSON.
- Success and client error codes: yes, 200, 201, 204, 400, 401, 404, 409 are included.
- Input validation: yes, schemas specify types and formats such as `int64`, `string`, `email`, and `date-time`.
- Schemas reused: yes, using reusable components like `User`, `Poll`, `PollOption`, `Vote`, and input variants.
- Valid YAML syntax: the file is written as valid OpenAPI YAML.

## Notes on authentication

`openapi.yaml` currently includes authentication-related definitions in comments. The spec is prepared to support token-based authorization, but the security sections are currently disabled in the file.

To fully satisfy the original token-auth requirement, uncomment and implement the `bearerAuth` security scheme and require it on protected endpoints.

## Files

- `schema.sql` — database table definitions
- `openapi.yaml` — API endpoint and schema definitions

## Next steps

- Implement backend endpoints to match `openapi.yaml`.
- Add token authentication support and enable the security sections.
- Optionally add a computed results endpoint implementation for `/polls/{pollId}/results`.
