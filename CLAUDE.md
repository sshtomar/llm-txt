---

# CLAUDE.md

## About CLAUDE.md Files
The CLAUDE.md file provides hierarchical and updatable instruction management across repositories and users. This file helps Claude understand user preferences and project-specific requirements.

### User Preferences
When creating a CLAUDE.md file, include a `# User Preferences` section that captures:
- User's experience level (e.g., product designer with little coding experience)
- Need for detailed explanations vs. concise responses
- Preference for incremental changes over large modifications
- Learning goals and desire for educational context
- Visual signal preferences (⚠️ for large changes, 🔴 for high-risk modifications)

### Learning Mode Guidelines
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

---

## Project Context

> **Project**: URL → `llm.txt` generator
> **Goal**: Given a docs/site URL, crawl politely, extract clean Markdown, synthesize a concise `llm.txt` (and optional `llms-full.txt`), then return downloadable artifacts or open a PR.
> **Success**: P50 ≤ 90s/job, deterministic output within size cap, passes lint/tests, respects robots, minimal user friction.

---

## How you (Claude) should help

* Start by **reading** repo docs/config before writing code. Summarize your plan; then implement iteratively. Prefer small, reviewable changes.
* Use our **scripts and commands** (below). Ask before introducing new stacks. If you need a tool, propose it with rationale.
* Default to **deterministic behavior** (seeded, temperature 0 where applicable).
* Keep outputs within `MAX_KB` and prefer dropping low-signal pages (e.g., changelogs) over core docs.
* Always respect **robots.txt**; if blocked, stop and surface a clear message with alternatives (sitemap upload).
* Please do not generate any dummy data, UI component.

---

## Repo layout (conventions)

```
/api          # FastAPI/Express handlers (POST /v1/generations, GET /status)
/worker       # crawl → extract → summarize → compose pipeline
/crawler      # sitemap discovery, polite fetch, JS fallback (Playwright)
/composer     # llm.txt assembly, size budgeting, redaction
/cli          # optional local CLI wrapper
/web          # minimal Next.js landing + job status
/.claude      # Claude Code config & custom slash commands
```

Claude: if files differ, auto-discover entry points (`pyproject.toml`, `package.json`, `docker-compose.yml`) and adapt. Ask if uncertain.

---

## Commands (run these)

### Bash

* `make dev` — run API and worker locally (hot reload)
* `make test` — run unit + integration tests
* `make typecheck` — mypy/pyright or tsc
* `make fmt` — formatters (ruff/black or biome/prettier)
* `make gen URL=https://docs.example.com DEPTH=2 FULL=false` — run a full generation locally


---

## Code style & workflow

* Python: type hints required; prefer `ruff + black`; raise on warnings in CI.
* TS/JS: ES Modules only; strict TS; no default exports in libs.
* **Workflow**: explore → plan → code → test → commit. Prefer single-test runs for speed; typecheck before large edits. ([Anthropic][1])

---

## Testing

* Unit tests for: URL parsing, dedupe, size budgeting, markdown composer.
* Integration fixtures: **static site**, **JS-heavy site (Playwright)**, **large docs**, **multilingual**.
* Add regression tests when a bug is fixed.
* Claude: propose tests before refactors; run them; paste failing output when asking for help. (Claude Code’s plan-then-execute patterns improve reliability.) ([Anthropic][1])

---

## Tooling & permissions (Claude Code)

* **Always allowed**: `Edit`, `Bash(make *|pytest|npm run *|uv run *)`, `Git` (read), `gh` (read).
* **Ask first**: `Git commit`, `git push`, network calls beyond the target URL, Playwright browser automation.
* Configure via `/permissions` during a session or edit `.claude/settings.json`. Keep project settings in VCS. ([Anthropic][1])

> Install GitHub CLI (`gh`) to let Claude open PRs or inspect issues smoothly. ([Anthropic][1])

---

## MCP & external tools (optional)

If present, Claude may use these **MCP** servers via `.mcp.json`:

* `puppeteer` (JS rendering), `sentry` (observability), `github` (repo ops).
* Launch with `--mcp-debug` if config issues appear.
  MCP makes project tools discoverable and safer to use across the team. ([Anthropic][1])

---

## Data handling & safety

* Strip secrets/PII patterns from outputs; never include tokens or cookies.
* Respect `robots.txt`; throttle politely; exponential backoff on 429/5xx.
* On block: stop crawl and return actionable remediation.
  (These governance notes help Claude act safely when agentically using shell/tools.) ([Anthropic][1])

---

## Passing context to Claude Code

* Paste short logs directly, or `cat file | claude` for long logs.
* Ask Claude to read files/URLs it needs, or run tool `--help` first to learn usage.
  These are recommended context-passing patterns for Claude Code. ([Anthropic][1])

---

## Headless/CI usage

* Use **headless mode** for non-interactive tasks (CI hooks, triage):

  * `claude -p "<prompt>" --output-format stream-json`
  * Prefer quiet mode in production; add `--verbose` only for debugging.
* Example: issue triage, subjective linting, nightly `llm.txt` regen. ([Anthropic][1])

---

## Custom slash commands

Create reusable prompts in `.claude/commands/…`:

**`.claude/commands/gen-llm-txt.md`**

```
Regenerate llm.txt for: $ARGUMENTS

Steps:
1) Read crawler and composer configs.
2) Fetch and extract pages (respect robots).
3) Summarize with temp=0; enforce MAX_KB; spill to llms-full.txt if needed.
4) Run tests: composer, size budget, redaction.
5) If clean, commit with message "chore: regen llm.txt for $ARGUMENTS" (ask before pushing).
```

**`.claude/commands/fix-build.md`**

```
Analyze failing CI. Use `gh run view --log-failed`, propose a fix, implement, and re-run targeted tests.
```

Slash commands make repeatable workflows one-keystroke actions. ([Anthropic][1])

---

## Prompts & thinking budget

* Be **specific and directive** in first attempts; it reduces back-and-forth.
* For complex refactors/migrations, use extended thinking models/features and ask Claude to **plan → execute → verify** explicitly. ([Anthropic][1], [Anthropic][3])

---

## Git & GitHub etiquette

* Small commits with descriptive messages; reference issues.
* Use `gh` for PRs; let Claude draft messages after reviewing diffs and history.
* Ask Claude to resolve simple review comments and push updates. ([Anthropic][1])

---

## Definition of done (per change)

* Tests updated/passing, typecheck clean, lints clean.
* `llm.txt` diff reviewed; size limit respected; no blocked paths included.
* Docs/README updated if UX or API changed.

---

## Quick tasks you can run (examples)

* **Add `/v1/generations`**: validate JSON, enqueue job, return `202 + job_id`.
* **Implement size budgeting**: drop least-important sections first; log what was trimmed.
* **Playwright fallback**: detect heavy JS; render; respect timeouts; cache.
* **GitHub Action draft**: call our API on docs changes; (post-MVP) fetch artifacts and commit.

> When doing any of the above, Claude: explain your plan first, then execute in small steps and run the nearest tests before moving on. These stepwise patterns map to the recommended “explore, plan, code, commit” workflow. ([Anthropic][1])

---
