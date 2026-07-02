# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`daily-recall` (하루한문) is a **personal active-recall tool**, not a content publisher. Every day it generates one Korean backend interview Q&A, publishes it to a Notion DB, and pushes **only the question** (never the answer) to Slack. The whole design exists to force *answer-before-you-read* recall. Read `design.md` §"목적과 원칙" before any non-trivial change — the four principles there are load-bearing, and "improvements" that violate them defeat the tool's purpose.

## Commands

```bash
pip install -r requirements.txt

python -m src.pipeline --mock                    # offline path check — no API/Notion needed
python -m src.pipeline --dry-run                 # real generation, prints markdown, no Notion
python -m src.pipeline --publish                 # real publish (idempotent)
python -m src.pipeline --publish --category network   # pin category (slug)
python -m src.pipeline --dry-run --seed 42       # reproducible RNG
python -m src.pipeline --init-db --parent-page <PAGE_ID>   # one-time: create the Notion DB
```

There is **no test suite** and no linter configured. `--mock` is the offline smoke test (runs the full selector→validate→render path with a fixture, no API key required); use it to verify changes that don't touch live Notion/Gemini calls.

Secrets come from `.env` locally (copy `.env.example`) and GitHub Actions Secrets in CI: `GEMINI_API_KEY`, `NOTION_API_KEY`, `NOTION_DB_ID` (required), `SLACK_WEBHOOK_URL` (optional). Scheduling is `.github/workflows/daily.yml`, cron `0 22 * * *` UTC = 07:00 KST.

## Pipeline architecture

`src/pipeline.py` orchestrates a 5-stage flow; each stage is a separate module:

1. **selector** (`selector.py` + `state.py`) — weighted-random category and difficulty, plus loads history/seeds/review-cue into a `GenerationContext`.
2. **generator** (`generator.py`) — Gemini API in **JSON mode** (`response_mime_type=application/json` + `response_schema`) to guarantee a structured `QAItem`. Validates against `QAITEM_SCHEMA`; retries once, then falls back to a second model.
3. **renderer** (`renderer.py`) — `QAItem` → standard markdown, and → Notion blocks / Slack blocks.
4. **notion_pub** (`notion_pub.py`) — creates the Notion DB page (idempotent: skips if today already published).
5. **slack_pub** (`slack_pub.py`) — pushes question-only Slack message after publish.

`_publish_flow` in `pipeline.py` is dependency-injected (state, generate_fn, publisher, slack_fn passed in) so the orchestration is testable without real services.

## Key architectural facts

- **Notion DB is the single source of truth.** There is no local state file. Dedup, per-category count, review queue, and idempotency are all *derived from Notion queries* (`NotionState` in `state.py`). The CI runner is ephemeral; state survives because it lives in Notion. `EmptyState` is the cold-start stub used by `--dry-run`/`--mock`.

- **Notion 2025-09 API uses data sources.** Pages are created against a `data_source_id`, not a database id. `resolve_data_source_id()` derives it from `NOTION_DB_ID` (first source) unless `NOTION_DATA_SOURCE_ID` is set explicitly.

- **slug is the canonical category key.** `config/taxonomy.py` owns the `slug → (display_name, subtopics)` mapping. `QAItem`, history, and seed data all store the slug; display names appear only in Notion Title/Category and prompts. The generator **forces** `item["category"]`/`["difficulty"]` back to the context values — the context is authoritative, not the model output.

- **Controlled markdown subset only.** `renderer.py` emits a fixed subset (H1–H3, paragraph, `**bold**`, `` `code` ``, fenced code blocks, `-` bullets, `---`, `>` quotes) and `md_to_notion.py` parses *only* that subset — it is not a general markdown parser. Critically: **no markdown tables** (the system prompt forbids them; the converter would break them). This subset is also the contract for future (Phase 5) video-script reuse, so avoid Notion-specific syntax.

- **Active-recall invariants (do not break).** The markdown template's `---` divider, the "먼저 스스로 답하라" hint, and answer-at-bottom placement are load-bearing, not decoration. Slack messages carry question + concept hints + Notion link **only** — never `answer_core`/`answer_deep`/`follow_ups` (see `to_slack_blocks`).

- **Resilience.** Generation: model chain (`MODEL` → `MODEL_FALLBACK`), one retry each. On total generation/publish failure, `publish_error` writes a `Kind=error` page to Notion and re-raises so the scheduler registers failure. Slack is a *secondary* notification: its exceptions are swallowed and never invalidate a successful publish.

## Tuning constants

`config/settings.py` holds tunables: `MODEL`/`MODEL_FALLBACK` (env `DR_MODEL`/`DR_MODEL_FALLBACK`), `difficulty_weights(count)`, `PAST_QUESTIONS_CAP`, `SEED_FEWSHOT_K`, `REVIEW_LOOKBACK_DAYS`, `SEND_SLACK` (auto = `bool(SLACK_WEBHOOK_URL)`). `config/taxonomy.py` holds `CATEGORY_WEIGHTS` — adjust only to shore up *weak areas*, not to indulge interests (per design.md).
