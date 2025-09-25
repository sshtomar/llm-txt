# Repository Guidelines

This document is a concise guide for contributors to llm-txt. It covers structure, workflows, and expectations so changes remain consistent and easy to review.

## CLAUDE.md File
The CLAUDE.md file provides hierarchical and updatable instruction management across repositories and users. This file helps Claude understand user preferences and project-specific requirements.

### User Preferences Section
When creating a CLAUDE.md file, include a `# User Preferences` section that captures:
- User's experience level (e.g., product designer with little coding experience)
- Need for detailed explanations vs. concise responses
- Preference for incremental changes over large modifications
- Learning goals and desire for educational context
- Visual signal preferences (⚠️ for large changes, 🔴 for high-risk modifications)

### Learning Mode Guidelines
I would benefit most from an explanation style in which you frequently pause to confirm, via asking me test questions, that I've understood your explanations so far. Particularly helpful are test questions related to simple, explicit examples. When you pause and ask me a test question, do not continue the explanation until I have answered the questions to your satisfaction. I.e. do not keep generating the explanation, actually wait for me to respond first. Thanks!

For users in learning mode, the CLAUDE.md should specify:
- Providing educational context and explanations for complex topics
- Breaking down changes into digestible parts
- Explaining reasoning process and why things work
- Adding verbose explanations when teaching new concepts
- Step-by-step breakdowns with additional comments
- Warnings for auto-accepting larger or complex code changes
- Clear visual signals for different risk levels
- Pausing for confirmation before significant modifications

### Benefits of CLAUDE.md
- **Hierarchical Structure**: Instructions cascade from user-level to project-level
- **Consistency**: Maintains consistent interaction style across sessions
- **Customization**: Tailors Claude's responses to user expertise and preferences
- **Safety**: Adds appropriate warnings and checkpoints for riskier changes
- **Education**: Facilitates learning through detailed explanations when needed

## Project Structure & Module Organization
- `llm_txt/` — Python package
  - `api/` FastAPI app (`llm_txt.api:app`)
  - `cli/` CLI entrypoint (`llm-txt` → `llm_txt.cli:main`)
  - `crawler/` Sitemap/robots crawling and fetching
  - `composer/` Text composition for `llm.txt` and `llms-full.txt`
  - `worker/` Background job lifecycle and models
- `tests/` — Pytest suite (`test_*.py`)
- `web/`, `web_codex/` — Frontend assets (if iterating on UI)
- Key files: `pyproject.toml`, `Makefile`, `.env(.example)`, `README.md`

## Build, Test, and Development Commands
- `make install` — Install package (editable) + dev deps; installs Playwright.
- `make dev` — Run API locally at `http://localhost:8000` (Uvicorn reload).
- `make test` — Run tests with pytest (`-v`).
- `make typecheck` — Run mypy against `llm_txt/`.
- `make fmt` — Format with Black and autofix lint with Ruff.
- CLI example: `llm-txt generate --url https://docs.example.com --full`.
- One-off: `python -m llm_txt.cli generate --url <URL> --max-pages 50`.
- Frontend (optional): `cd web_codex && npm install && npm run dev` (Next.js at `http://localhost:3000`).

## Coding Style & Naming Conventions
- Python 3.9+. Use 4-space indents, Black (line length 88), Ruff, and mypy.
- Modules and files: `snake_case.py`; classes: `PascalCase`; functions/vars: `snake_case`.
- Add docstrings (`"""..."""`) for public modules, classes, and functions.
- Keep functions small; prefer explicit names and typed signatures.

## Testing Guidelines
- Framework: pytest (+ pytest-asyncio when needed).
- Place tests in `tests/` and name `test_*.py`; test functions start with `test_`.
- Write unit tests for new logic in `crawler`, `composer`, `worker`, `api`, and CLI.
- Run locally with `make test` or `pytest -k <keyword>` when iterating.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject (≤72 chars), body explaining rationale and impact.
- Reference issues (e.g., `Fixes #123`) when applicable.
- PRs must include: clear description, scope of change, test coverage notes, manual test steps, and any relevant screenshots (for UI).
- Ensure `make fmt`, `make typecheck`, and `make test` pass before requesting review.

## Security & Configuration Tips
- Secrets: set in `.env` (e.g., `ANTHROPIC_API_KEY`); never commit secrets.
- Crawling: default respects robots.txt; use `--no-robots` only for controlled testing.
- Keep external requests polite (rate limits) and deterministic in tests (mock I/O).
