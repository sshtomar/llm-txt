Regenerate llm.txt for: $ARGUMENTS

Steps:
1) Read crawler and composer configs.
2) Fetch and extract pages (respect robots).
3) Summarize with temp=0; enforce MAX_KB; spill to llms-full.txt if needed.
4) Run tests: composer, size budget, redaction.
5) If clean, commit with message "chore: regen llm.txt for $ARGUMENTS" (ask before pushing).