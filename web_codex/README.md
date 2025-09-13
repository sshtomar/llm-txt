llm.txt Frontend (web_codex)

Dev-focused Next.js UI for the llm.txt generator.

Quick start

- Set `NEXT_PUBLIC_API_BASE_URL` to your API origin (or leave empty if serving from same origin)
- Install deps: npm install
- Run dev: npm run dev

Berkeley Mono font

- The UI prefers Berkeley Mono when available. Due to licensing, font files are not bundled.
- Option A (variable font): copy `BerkeleyMono-Variable.woff2` into `web_codex/public/fonts/`.
- Option B (static): copy `BerkeleyMono-Regular.woff2` into `web_codex/public/fonts/`.
- Option C (trial OTF): copy `BerkeleyMonoTrial-Regular.otf` into `web_codex/public/fonts/`. OTF works, but WOFF2 is recommended for performance.
- Or install the font system‑wide; we try multiple local names (Berkeley Mono, BerkeleyMono, Berkeley Mono Trial).
- After adding, restart dev and verify in DevTools → Rendered Fonts that Berkeley Mono is used.

Keyboard shortcuts

- Ctrl+Enter: submit job
- Ctrl+D: download active preview
- Ctrl+C: copy preview to clipboard
- /: focus search in preview

Notes

- Polls `/v1/generations/:id` for progress; downloads preview via `/v1/generations/:id/download/(llm.txt|llms-full.txt)`
- Theme persists in localStorage; dark by default
- Tailwind + monospace, terminal-inspired aesthetic per CLAUDE_FRONTEND.md
