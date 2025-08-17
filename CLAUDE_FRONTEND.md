---

# CLAUDE.md — Frontend (Next.js) Guide

> **Project:** URL → `llm.txt` generator
> **Goal:** Ship a fast, minimal landing page with an interactive generator card (paste URL → preview `llm.txt` → download / open PR).
> **Success:** Core flow works locally in ≤10 minutes; clean diffs; a11y + performance sane by default.

---

## How you (Claude) should work here

1. **Read before changing:** scan `package.json`, `next.config.js`, `app/**`, `components/**`, `lib/**`, `tailwind.config.ts`.
2. **Plan → apply small diffs:** propose a short plan, then implement in *small, reviewable* changes.
3. **Prefer reuse:** add components to `components/ui/*`; keep business logic in `lib/*`.
4. **Determinism & safety:** do not introduce network calls beyond our own `/api` routes. No secrets in client.

---

## Stack & conventions

* **Framework:** Next.js (App Router), React 18, TypeScript **strict**.
* **Styling:** TailwindCSS; small design tokens in `tailwind.config.ts`.
* **UI kit:** lightweight custom components; ok to add shadcn/ui (only what we use).
* **Icons:** `lucide-react`.
* **Pkg mgr:** `pnpm`. Node LTS.

### Project structure

```
web/
  app/
    (marketing)/
      page.tsx                 # Landing + inline demo
      pricing/page.tsx
      privacy/page.tsx
    generate/page.tsx          # Full generator (advanced options)
    status/[jobId]/page.tsx    # Job status/preview
    api/                       # Stubbed API routes for local demo (fetch server)
  components/
    hero.tsx
    generator-card.tsx
    url-input.tsx
    options-panel.tsx
    preview-panel.tsx
    job-steps.tsx
    navbar.tsx
    footer.tsx
  lib/
    api.ts                     # typed fetchers (POST /v1/generations, GET /status)
    validators.ts              # zod URL/params
    constants.ts
```

---

## Commands (run these)

```bash
pnpm i                 # install
pnpm dev               # start Next.js (http://localhost:3000)
pnpm test              # unit tests (vitest)
pnpm e2e               # Playwright e2e
pnpm lint && pnpm typecheck && pnpm format
```

> Claude: use these commands via shell; paste failing output when asking for changes.

---

## Primary tasks (MVP UI)

1. **Landing hero (urlbox-style)**

   * Big headline, subhead, URL input, **Generate** button.
   * Microcopy: *“Respects robots.txt. First file free—no signup.”*
   * Right side: **GeneratorCard** with options toggle and live preview.

2. **Generator card**

   * Inputs: `url`, `depth (1–3)`, `exclude paths`, `maxKB`, checkbox `llms-full.txt`.
   * CTA: **Generate** → call `/api/generate` (stub) → show preview + job id.
   * Secondary: **Download**, **Copy**, **Open PR** (disabled in MVP).

3. **Status page**

   * Steps: *Queued → Crawling → Summarizing → Composing → Done*.
   * Poll `/api/status/{jobId}`; when done, show tabs for `llm.txt` / `llms-full.txt`.

4. **Pricing & basics**

   * Simple 3-tier grid (Free / Pro / Team).
   * Footer links: Privacy, Terms (placeholder).

---

## UX rules

* **One job, one control:** URL + one clear primary CTA in the hero.
* **Optimistic UI:** disable CTA while running; show skeleton preview.
* **Errors:** inline, human-readable; keep previous inputs intact.
* **Keyboard-first:** URL input auto-focused; Enter triggers Generate.
* **Copy affordances:** “Copy `llm.txt`” button with toast.

---

## API usage (frontend)

Use our typed fetchers in `lib/api.ts`:

```ts
export type GenerateBody = {
  url: string;
  depth?: number;
  includeFull?: boolean;
  blockedPaths?: string[];
  maxKB?: number;
};

export async function createGeneration(body: GenerateBody) { /* fetch('/api/generate') */ }
export async function getStatus(jobId: string) { /* fetch(`/api/status/${jobId}`) */ }
```

**Never** call third-party domains from the client.

---

## Visual design notes

* **Layout:** max-w-6xl center; generous white space.
* **Color:** soft indigo → white gradient background on hero only.
* **Card:** glassy card (rounded-2xl, shadow-lg, border, subtle backdrop blur).
* **Type:** tight headline (tracking-\[-0.02em]), secondary text at 80% opacity.
* **Preview:** monospace, line numbers (CSS counters), copy button.

---

## Accessibility & SEO

* WCAG AA color contrast; focus rings via Tailwind.
* Labels on all inputs; `aria-live="polite"` for status updates.
* `Metadata` in App Router; semantic headings; Open Graph tags.

---

## Performance

* No heavy UI libs.
* Debounce URL validation; lazy-load Playwright screenshots **only** if we ever add them.
* Use `next/script` for analytics (Plausible/Umami) post-MVP.

---

## Testing

* **Unit (Vitest + RTL):** `url-input`, `options-panel`, `preview-panel` states.
* **E2E (Playwright):** Happy path: enter URL → see preview; Error path: invalid URL; Status polling path.
* **Lints:** eslint (next/core-web-vitals), types, Tailwind class sorter.

---

## Allowed actions for Claude Code

**Allowed (no ask):**

* Edit files under `/web/**`, create new components, pages.
* Run `pnpm` scripts, jest/vitest, playwright, lint/format.
* Adjust Tailwind config & `globals.css`.

**Ask first:**

* Install new deps, add UI libraries, change Node/Next versions, add analytics.

---

## Custom slash commands (put in `.claude/commands/`)

**`build-hero.md`**

```
Create/improve landing hero:
- H1 “Paste a docs URL → get llm.txt.”
- Subhead one line.
- URL input + Generate CTA.
- Right: <GeneratorCard /> with options collapsed by default.
- Keep to 50 lines diff; Tailwind only; responsive md: grid-cols-2.
```

**`wire-generator.md`**

```
Implement GeneratorCard:
1) Use zod to validate url/depth.
2) Call lib/api.createGeneration, show spinner & disable CTA.
3) On success: render <PreviewPanel text={data.preview} jobId={data.jobId} />
4) Error: inline alert; keep prior input.
5) Add unit tests: submits, disables button, renders preview.
```

**`add-status-page.md`**

```
Create /status/[jobId]:
- Poll lib/api.getStatus every 1.5s (max 60s).
- Render stepper, final preview with Copy/Download.
- Handle failed status with retry CTA.
```

**`fix-a11y.md`**

```
Run eslint a11y; add labels/aria-live; ensure focus management after generate.
```

---

## Definition of done (frontend change)

* No console errors; types pass; lints clean.
* e2e happy path green.
* CLS < 0.02 on hero (no layout jank); Lighthouse perf ≥ 90 on desktop.
* Copy/Download work in the preview; responsive at 360px width.

---

## Copy deck (defaults)

* **H1:** “Paste a docs URL → get `llm.txt`.”
* **Sub:** “Make your site AI-friendly in under 90 seconds.”
* **CTA:** “Generate `llm.txt`”
* **Form help:** “We respect robots.txt. First file free—no signup.”

---

## Small backlog (feel free to pick up)

* Add `Diff` tab to preview when `existingLlmTxt` is present.
* “Trim report” callout when size cap prunes sections.
* Pricing grid + FAQ section on `/pricing`.
* Toasts via a tiny `useToast` hook.

---

If anything in the repo deviates from this guide (folder names, scripts), **summarize differences first**, then adapt your plan.
