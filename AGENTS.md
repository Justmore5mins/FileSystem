# Repository Guidelines

## Project Structure & Module Organization

- `src/main.py` contains the Flask application, routes, static-file handling, and security headers.
- `src/filesystem/` contains the installable package entry point.
- `public/` contains browser assets served by the application, including `index.html` and `style.css`.
- `database/` contains the SQLite metadata database and stored files. Treat its contents as application data, not source code.
- `test.sql` contains database-oriented test/setup SQL. Add automated Python tests under `tests/` as functionality grows.

## Build, Test, and Development Commands

Use the project’s `uv` environment where possible:

```sh
uv sync                              # Install locked dependencies
uv run -m src.main
uv build                             # Build the Python package
uv run pytest                        # Run tests, when tests are present
```

The application currently has no committed test suite, so verify UI and file-serving changes manually at `http://localhost:80/` and inspect response status/content types.

## Coding Style & Naming Conventions

Use four-space indentation and standard Python formatting. Prefer descriptive `snake_case` names for functions and variables; retain existing class-style names only when matching established code. Keep Flask route handlers small, parameterize SQL values, and use `pathlib.Path` for filesystem paths. Use lowercase kebab-free filenames for web assets, such as `style.css`.

## Testing Guidelines

Place tests in `tests/`, name files `test_*.py`, and use pytest with Flask’s test client for route behavior. Cover successful and missing-file responses, redirects, content types, and security headers. Never use production database data for destructive tests; create an isolated temporary database.

## Commit & Pull Request Guidelines

No Git commit history is currently available in this checkout, so no existing message convention can be confirmed. Use concise imperative subjects (for example, `Fix static stylesheet path`) and keep unrelated changes separate. Pull requests should explain the behavior change, list verification commands, mention database or configuration effects, and include screenshots for visible UI changes.

## Security & Configuration Tips

Keep the Content Security Policy restrictive, continue using parameterized SQL, and validate file names before serving database-backed files. Do not commit secrets, local credentials, or newly generated database contents without a clear reason.
