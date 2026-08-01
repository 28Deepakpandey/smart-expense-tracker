# AI Notes

This document explains how AI assistance (Claude) was used while building
this project. We're being specific and honest here rather than writing a
generic "AI helped with some parts" statement, since that wouldn't be
useful to a reviewer — and wouldn't be truthful either.

## How We Worked

Given the 48-hour turnaround, we used Claude to draft the full first
version of the codebase directly from this assignment's requirements —
the module structure, the endpoints, the storage layer, and the test
suite. We did not write the code from scratch ourselves and then use AI
only for polish; the honest description is that AI drafted it and we
reviewed, ran, and made the final decisions on all of it. What follows
is what "reviewed" actually meant in practice, not a claim that we wrote
these files by hand.

Before finalizing, we:

- Ran `pytest tests/ -v` and confirmed all 16 tests pass.
- Copied the project to a separate directory containing only the files
  meant for the repository (no `.venv`, no `__pycache__`) and re-ran the
  exact install/run/test commands from `README.md` on that clean copy,
  to make sure they work verbatim and not just in our working directory.
- Started the server and manually exercised every endpoint (add three
  expenses, list, filter by category, get the summary, get the monthly
  summary, delete, delete-again-to-confirm-404, submit an invalid
  amount) and used the real output — not hand-written example text — for
  the README's example requests/responses.

## 1. AI-Generated vs. Reviewed/Decided by Us

Everything in `src/` and `tests/` was AI-drafted in the first pass. Our
contribution was reviewing that output against the assignment brief and
making the following calls, each of which we could justify if asked:

- **Kept** the four-module split (`models.py`, `storage.py`,
  `service.py`, `main.py`) because it keeps route handlers thin and
  makes `service.py` unit-testable without going through HTTP. This
  matched the assignment's "modular structure" requirement without
  adding layers a 5-endpoint API doesn't need.
- **Kept** the `threading.Lock` around file reads/writes in
  `storage.py`. We considered removing it as unnecessary for a
  single-process demo, but a JSON-file-per-write approach is
  susceptible to two concurrent requests corrupting the file, and the
  lock costs one import and three lines — worth keeping.
- **Kept** case-insensitive category matching (`"Food"` matches
  `?category=food`) as the more forgiving, more realistic behavior for
  a filter parameter, and added a dedicated test for it so the behavior
  is locked in rather than incidental.
- **Kept** `round(..., 2)` on both summary calculations. Summing floats
  (e.g. amounts like `0.1 + 0.2`) can produce results like
  `0.30000000000000004` in Python; rounding to 2 decimal places avoids
  surfacing that as a visible bug in a money-related API.
- **Added** two empty-state tests
  (`test_summary_with_no_expenses_is_zero`,
  `test_get_expenses_empty_list_when_none_created`) after checking what
  a reviewer's very first request against a fresh checkout would return
  — before any expense has ever been added.

## 2. What We Validated, Tested, or Changed, and Why

- **We did not trust "the tests should pass."** We ran them, on a clean
  checkout, using the exact command in the README, and only wrote "16
  tests, all passing" in this document after seeing that output
  ourselves.
- **We did not trust the drafted README example payloads as accurate.**
  Rather than leaving Claude's illustrative JSON in the README, we
  called the real endpoints via `TestClient` (add expenses, list,
  filter, summarize, delete) and replaced every example in the README
  with actual output from those calls, including exact totals like
  `78.25` and the monthly breakdown.
- **We checked the clean-checkout scenario specifically**, because the
  assignment says submissions will be run "exactly as written." Testing
  only in our already-set-up working directory (with a `.venv` and
  cached files already present) would not have caught a command that
  only works by accident because of leftover local state.
- **We manually confirmed the 404 delete path and the 422 validation
  path** return the status codes and bodies documented in the README,
  rather than assuming FastAPI's default behavior matches what we wrote
  down.

## 3. AI Suggestions We Did Not Use

- **A database (SQLite via SQLAlchemy) instead of a JSON file.** Claude
  raised this as a "more realistic" persistence option. We rejected it:
  the assignment explicitly allows in-memory or local-file storage, and
  a database would add ORM setup, migrations, and configuration that a
  4-hour, single-collection assignment doesn't need. This is exactly
  the kind of over-engineering the brief asked us to avoid.
- **A `GET /expenses/{id}` endpoint "for completeness."** The
  assignment doesn't ask for it, and adding an unrequired endpoint just
  because it's conventional REST would mean untested surface area with
  no stated use case. We left it out.
- **Splitting `main.py` into a per-resource `routers/` package.** With
  five endpoints on a single resource, a router package would add
  indirection (more files to open to trace one request) without a real
  benefit at this scale. We reserved the module split for the concerns
  that are genuinely separate — models, storage, and business logic —
  and kept the routes themselves in one file.
- **Docker support as the bonus feature.** We considered it, but chose
  the monthly summary endpoint instead. It reuses the same aggregation
  pattern already needed for `total_by_category`, needs no new
  dependencies, and gives a reviewer real data to query, which felt
  like a better use of the assignment's limited scope than a
  Dockerfile that just wraps `uvicorn`.
- **A custom `ExpenseNotFoundError` exception with a registered FastAPI
  exception handler**, suggested for the delete-not-found case. For a
  single error case in a small API, a direct
  `raise HTTPException(...)` in the route is more transparent to read
  than an indirection layer built for one exception type, so we kept
  it inline instead.
