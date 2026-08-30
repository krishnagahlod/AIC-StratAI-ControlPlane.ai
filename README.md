# ControlPlane.ai

**A real-time AI oversight layer that catches hallucinations, cost waste, and responsibility
violations before they become incidents — and translates every flag into business impact,
a graduated escalation decision, and a plain-English report for the right audience.**

Built by **Team StratAI** (IIT Bombay) for the Accenture Innovation Challenge 2026 — Round 2
prototype for Problem Track 1, ControlPlane.ai.

---

## 1. What this actually is

Enterprises run generative AI across many use cases at once — a customer-facing support bot,
an internal knowledge copilot, a decision-support tool — each with a different risk tolerance
and latency budget. This prototype sits as a reverse proxy in front of those applications' LLM
calls and, for every request/response pair:

1. **Runs fast, synchronous safety checks** (PII redaction, jailbreak blocklist, budget
   enforcement) before the response reaches the user — genuinely low-latency, regex-based.
2. **Runs a deeper, asynchronous evaluation** across three dimensions — **Performance**
   (hallucination/faithfulness), **Cost** (waste, redundant calls, model-task mismatch), and
   **Responsibility** (PII, bias, toxicity, safety, prompt injection) — after the response is
   already delivered, so it never slows the user down.
3. **Computes a composite TrustScore**, translates flagged issues into **estimated dollar
   business impact**, applies **tiered human escalation with an SLA countdown** (not binary
   block/allow), generates **prescriptive fixes**, and can **backtest a proposed blocking
   policy** against labeled historical traffic before it's ever deployed.

Everything described below is **working code you can run**, not a mockup — see [§5](#5-running-it).

---

## 2. Architecture

```
AI App (support bot / copilot / decision tool)
        │  POST /v1/chat/completions  (OpenAI-compatible)
        ▼
┌───────────────────────────── DATA PLANE (backend/app/proxy) ─────────────────────────────┐
│ Sync checks (regex, in-process): PII redact → jailbreak blocklist → budget gate            │
│ Forwards sanitized prompt to Gemini → output PII/toxicity quick-check → returns response    │
└───────────────────────────────────────┬───────────────────────────────────────────────────┘
                                         │ background task (non-blocking)
                                         ▼
┌────────────────────────── CONTROL PLANE (backend/app/evaluation) ────────────────────────┐
│ Performance Analyzer   — deterministic numeric-claim check + LLM-as-judge faithfulness      │
│ Cost Analyzer          — deterministic token pricing + rule-based complexity classifier     │
│ Responsibility Analyzer— deterministic PII/leak regex + LLM-as-judge bias/toxicity/safety    │
└───────────────────────────────────────┬───────────────────────────────────────────────────┘
                                         ▼
┌───────────────────────── INTELLIGENCE LAYER (backend/app/intelligence) ──────────────────┐
│ TrustScore (weighted per-app) → Business Impact ($) → Smart Escalation (+SLA timer)         │
│ → Prescriptive Actions → Executive Narrator (per-audience) → Policy Playground (backtest)   │
└───────────────────────────────────────┬───────────────────────────────────────────────────┘
                                         ▼
┌───────────────────────────── PRESENTATION (frontend/, Next.js) ──────────────────────────┐
│ Overview · Live Feed & Trace Explorer · Trends · Business Impact & Exec Brief ·             │
│ Human Review Queue · Policy Playground · Try It Live                                        │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

This condenses the original 4-layer / 17-node architecture design (see `docs/`) into one
unified dashboard rather than three separate presentation surfaces — a deliberate scope choice
for this round, not a capability gap (each concept below still exists and is independently
addressable via the API).

---

## 3. What's real, what's simplified — and why

Round 2 explicitly asks teams to state assumptions and justify *when* something uses
deterministic logic vs an LLM. Here's the honest breakdown:

| Check | Method | Why |
|---|---|---|
| Input/output PII, jailbreak blocklist, data-leakage (API keys, internal URLs) | **Deterministic regex** | Must be fast enough to sit on the synchronous path; regex is genuinely sub-millisecond. |
| Numeric-claim hallucination (response cites a number absent from source context) | **Deterministic** (regex extraction + set comparison) | A quantitative check should not depend on an LLM's own judgment. |
| Semantic faithfulness, contradiction, completeness, coherence | **LLM-as-judge** (Gemini) | No reliable automated ground truth exists for open-ended claims — this is explicitly one of the Round 2 brief's sanctioned techniques. Output is labeled `method: "llm_judge"` everywhere in the API/UI so it's never confused with a deterministic signal. |
| Token cost, pricing, task-complexity classification (→ model-overuse detection) | **Deterministic** (real token counts × a pricing table, keyword-based complexity heuristic) | Cost math must not be LLM-generated — the Round 2 brief calls this out directly. |
| Bias, toxicity, safety-policy violation, prompt-injection (paraphrased) | **LLM-as-judge** | These require semantic understanding a regex can't provide. |
| Business Impact ($) | **Deterministic formula** over stated assumptions (below) | A rule-based mapping table (flag type → risk category → $ formula), not LLM-generated numbers. |
| Executive Narrator text | **LLM-generated prose** over the deterministic stats above | The *numbers* are never invented by the LLM; only the sentence wrapping them is. |

**Stated business assumptions** (`backend/app/config.py: BUSINESS_ASSUMPTIONS`) — illustrative,
not sourced from a real company, as the brief permits: average order value $85, customer
lifetime value $620, ~12,000 weekly interactions per app, GDPR fine reference of $20M at a
0.04% per-incident probability, etc. Every number the Business Impact Scorer produces is
traceable to one of these constants plus the interaction's own metadata — nothing is a magic
number embedded in prose.

**Infrastructure simplifications**, made deliberately to fit the time budget without hiding
the tradeoff:
- **SQLite**, not Postgres — zero setup for a reviewer running this locally.
- **In-process Python state**, not Redis/Celery — budget counters and the redundant-call/
  agent-loop cache are in-memory dicts; async evaluation dispatch uses FastAPI's
  `BackgroundTasks` + `asyncio.to_thread` rather than a real message queue.
- **No Presidio/Detoxify model downloads** — PII detection is a curated regex module; toxicity/
  bias/safety use Gemini as an LLM-as-judge instead of a fine-tuned classifier. This was a
  direct tradeoff against multi-GB model downloads eating the build's time budget.
- **Escalation SLA windows are compressed** from the architecture's "5 minutes" to 120s
  (standard escalation) / 30s (forced critical block) so the safe-default behavior is
  observable live in a demo instead of requiring a real wait.
- **Historical seed data is deterministic, not LLM-generated** — `backend/app/seed/seed_data.py`
  writes ~165 pre-authored request/response pairs (a mix of clean and intentionally-flawed
  scenarios with hand-labeled ground truth) directly through the *real* scoring/business-impact/
  escalation code paths, so the dashboard has rich, reproducible history without burning API
  quota. **The "Try It Live" page is the one path that makes genuine Gemini calls** through the
  full pipeline end-to-end.
- **Free-tier Gemini rate limits are real and were hit during development** (5 requests/minute
  on `gemini-2.5-flash`). The judge/narrator calls were deliberately routed to the cheaper
  `gemini-2.5-flash-lite` tier, and every LLM-as-judge call degrades to "no signal from this
  check" on any upstream failure rather than crashing the evaluation pipeline — see
  `backend/app/proxy/llm_client.py`.

---

## 4. Tech stack

- **Backend**: Python, FastAPI, SQLAlchemy + SQLite, `google-genai` SDK (Gemini 2.5 Flash /
  Flash-Lite).
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind CSS 4 + Recharts.
- **No Docker requirement** — plain `uvicorn` / `npm run dev`.

### Design system

The UI follows an Accenture-style enterprise visual language: light theme, the brand purple
(`#A100FF`, with `#7500C0` as the text/hover-safe deep variant) as the sole accent, and Public
Sans as the UI typeface — the closest free/open alternative to Graphik (a paid commercial font)
available on Google Fonts. The exact palette was extracted from a real Accenture-branded deck
(`ppt/theme/*.xml` color and font tables) rather than guessed.

Chart colors are not arbitrary: the categorical series palette (TrustScore/Cost/Performance/
Responsibility) was built and validated against Anthropic's `dataviz` skill's accessibility
checker (`validate_palette.js`) for CVD-safe adjacent-pair separation and contrast against a
white surface, and status/severity colors (the flag chips) are kept deliberately distinct from
the chart series palette so a status color never impersonates a series. The Trends page's
volume/cost chart was also split into two single-axis charts rather than one dual-axis chart,
per that skill's #1 anti-pattern rule (never two y-scales on one chart).

---

## 5. Running it

### Backend

```bash
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows; use `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

cp .env.example .env
# edit .env and set GEMINI_API_KEY=<your key> (https://aistudio.google.com/apikey)

python -m app.seed.seed_data   # populates ~165 historical interactions across 3 apps
uvicorn app.main:app --reload --port 8000
```

Backend is now live at `http://localhost:8000`. Try it:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What is your return policy?"}],
       "metadata":{"app_key":"customer_support_bot"},
       "rag_context":"Returns are accepted within 30 days with a valid receipt."}'
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # defaults to http://localhost:8000, change if needed
npm run dev                    # runs on http://localhost:3010 (fixed port, see package.json)
```

Open `http://localhost:3010`.

### Suggested walkthrough

1. **Overview** — fleet-wide TrustScore trend, budget usage per app, live alerts feed.
2. **Live Feed** — click any historical interaction to see its full evaluation trace
   (flags, sub-scores, business impact, escalation decision).
3. **Trends** — TrustScore and its three sub-dimensions over the last 14 days, filterable by app.
4. **Business Impact** — switch between Engineer / CISO / CEO to see the same underlying
   data narrated differently; dollar breakdown by risk category; prescriptive action list.
5. **Review Queue** — the escalation demo: the seed script leaves a couple of fresh
   `escalate_human` / `auto_block_alert` items with a live countdown to the SLA safe-default.
   Approve / Reject / Edit them, or wait for the timer to auto-default.
6. **Policy Playground** — drag the TrustScore threshold slider and watch precision/recall/F1
   recompute live against the 165 labeled historical interactions — this is the "don't deploy
   guardrails blind" story.
7. **Try It Live** — pick a preset (or write your own prompt + optional source context) and
   send a **real** request through the proxy to Gemini. Watch the sync response arrive
   instantly, then the async evaluation populate a few seconds later.

### Demo mode (optional)

The Review Queue's SLA windows are deliberately short (30–120s) — safe defaults apply
fast, which is the point. That makes the queue awkward to demo or record, because a
pending item can expire mid-walkthrough.

Setting `DEMO_MODE=1` in `backend/.env` enables two endpoints and a matching control in
the sidebar:

| Endpoint | Purpose |
|---|---|
| `GET /api/demo/status` | Reports whether demo mode is on |
| `POST /api/demo/arm-review-queue` | Re-opens three recent human-review escalations — chosen across different apps and decision types — with a 10-minute SLA |

It re-opens escalations that genuinely reached a human-review decision; it does not
fabricate interactions. Off by default, and documented here rather than hidden, because
an AI-governance tool should not ship an undisclosed way to manufacture its own state.

> **Recording note:** record against a production build (`npm run build && npm run start`),
> not `npm run dev`. The dev server renders an error-count badge in the bottom-left corner
> whenever any console error occurs, which will otherwise appear on camera.

---

## 6. Repository structure

```
controlplane-ai/
  backend/
    app/
      proxy/        — Data Plane: OpenAI-compatible endpoint, sync checks, Gemini client
      evaluation/    — Control Plane: performance/cost/responsibility analyzers + orchestrator
      intelligence/  — TrustScore, Business Impact, Escalation, Prescriptive Actions,
                       Executive Narrator, Policy Playground
      api/           — dashboard/review-queue/playground/narrator REST routes
      db/            — SQLAlchemy models
      seed/          — synthetic app definitions + deterministic historical data seeder
  frontend/
    app/             — Next.js pages (one per dashboard view)
    components/, lib/
```

---

## 7. Known limitations / what a production version needs next

- Multi-tenant auth on the proxy endpoint (currently open, single-process demo).
- A real message queue (Redis Streams/Celery) once evaluation volume exceeds one process.
- A fine-tuned or purpose-built classifier for toxicity/bias to reduce LLM-as-judge latency
  and cost at scale (the architecture explicitly supports swapping this in — the analyzer
  interfaces don't assume Gemini specifically).
- The human-review feedback loop currently *captures* reviewer decisions (`Escalation.reviewer_decision`)
  but does not yet feed them back into threshold recalibration — that's the natural next step
  once there's enough reviewed volume.
