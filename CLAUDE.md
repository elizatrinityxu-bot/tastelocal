# TasteLocal — Security Policy for AI Assistance

## Environment Variables & Credentials

- Never expose credentials outside of `.env`. All secrets (SECRET_KEY, DB_PASSWORD, API keys) must live exclusively in `.env`.
- Never print environment variables in logs, terminal output, or any response.
- Always load database credentials using `os.getenv()` or `os.environ.get()`. Never read them from any other source.
- Do not hardcode secrets inside `settings.py` or any other Python file. Fallback defaults in `os.environ.get("KEY", "default")` must never be real credentials.

## File Rules

- `.env` is git-ignored and must never be committed.
- `.env.example` is the public template — it must only contain placeholder values (e.g. `replace_me`), never real credentials.
- `settings.py` must always call `load_dotenv()` before reading any environment variable.
