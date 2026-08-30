# ControlPlane.ai — Prototype Improvement Implementation Plan

**Author:** Engineering, Team StratAI
**Date:** August 30, 2026, 17:05 IST
**Input:** [`docs/product_audit_report.md`](./product_audit_report.md) — 10 severity-ranked findings from a live, hands-on product audit
**Objective:** Take the prototype from "works, with visible cracks" to "presentable and unique," ready to be the hero of the Round 2 demo video.

---

## 0. Scope Reconciliation — Read This First

You chose a **~2.5 hour** prototype budget *and* **all four** optional additions. Those two choices do not both fit, and I'd rather say so now than discover it at 21:00 tonight:

| Bucket | Estimate |
|---|---|
| Audit fixes (5× P0, 2× P1, 2× P2) | **2h 12m** |
| Addition A — Live pipeline visualisation | 50m |
| Addition B — Richer seed data | 25m |
| Addition C — Demo Mode | 25m |
| Addition D — Compliance audit export | 30m |
| Final verification sweep (production build) | 20m |
| **Total if everything ships** | **≈ 4h 42m** |

Against ~7h of runway, with an Accenture-style deck and a demo video still to produce, a 4h 42m prototype phase leaves roughly **2h 20m for the two deliverables that currently do not exist at all.** That is the real risk, and it is a scheduling risk, not an engineering one.

**So this plan is gated, not linear.** Work is ordered strictly by *what a judge can see and what protects the video*, with two hard checkpoints where we decide whether to continue or hand off to the deck. Nothing gets silently dropped — you see exactly what falls below each line and choose.

**My recommendation:** commit to **Phase 1 + Phase 2** (≈ 3h 05m including verification). That ships every fix, plus the two additions that directly protect the recording. Then take the Checkpoint B decision on the pipeline visualisation with real information about how the clock is running, rather than guessing now.

---

## 1. Decisions Locked (from your answers)

| # | Question | Decision | Consequence for this plan |
|---|---|---|---|
| 1 | Prototype time budget | ~2.5h, gated as above | Phase structure in §3; Checkpoints A and B |
| 2 | Executive Narrator hallucination fix | **Prompt fix + self-grounding validator + UI badge** | W1 is the largest single work item and the plan's flagship — see §4.1 |
| 3 | Blocked-interaction TrustScore | **UI treatment, keep the scoring math** | W6; no changes to `trust_score.py`, no aggregate shifts |
| 4 | Additions wanted | **All four** | Sequenced across Phases 2 and 3 by demo leverage |

Two things I decided myself, flagged for visibility rather than asking:

- **Record against a production build** (`npm run build && npm run start`), not `npm run dev`. This is P0 #5 in the audit and needs no code — it is a runbook line, captured in §6.
- **The 390px mobile layout stays out of scope.** Already agreed previously; the video is desktop. Restating so it isn't re-raised as a new bug.

---

## 2. Guiding Principles for This Pass

These are the rules I'll hold myself to while making the changes, drawn from the same research the audit was graded against:

1. **Never let "loading" and "zero" look identical.** Every number that can be absent gets a distinct third state. This is the root cause of the audit's #4 and half of #2.
2. **Every failure must be visible in the UI, not the console.** `.catch(console.error)` is banned as a *terminal* error strategy anywhere a user is waiting on data. It can log, but something must also surface.
3. **Fix the class, not the instance.** The `$0` flash is one symptom of "no loading state"; the silent backend failure is one symptom of "no error channel." Both get fixed at the component/API-client level so they don't reappear on a page I didn't touch.
4. **Never fake data to look good.** Where the pipeline visualisation animates, every stage transition must be driven by a real backend signal. Illustrative timing is fine and will be labelled; invented state is not. Building a fake progress bar into a *governance* product would be the same class of sin as the narrator hallucination.
5. **Don't touch what the audit says is working.** The trace-detail panel, CEO/CISO narratives, Review Queue empty state, and Policy Playground are explicitly out of bounds except where a listed finding requires it.

---

## 3. Phase Structure & Cut Lines

| Phase | Contents | Duration | Running total | Gate |
|---|---|---|---|---|
| **Phase 1 — Credibility** | W1–W6: every P0 and P1, plus the two cheap P2s | 2h 12m | 2h 12m | **Checkpoint A** |
| **Phase 2 — Protect the shoot** | W7 (seed data), W9 (Demo Mode) | 50m | 3h 02m | **Checkpoint B** |
| **Phase 3 — Differentiate** | W8 (pipeline visualisation) | 50m | 3h 52m | — |
| **Phase 4 — Stretch** | W10 (compliance export) | 30m | 4h 22m | — |
| **Verification** | Production-build sweep, re-run audit script | 20m | 4h 42m | — |

**Checkpoint A (after Phase 1):** everything a judge could see as *broken* is fixed. If the clock has slipped badly, this is a legitimate stopping point — we hand off to the deck with a prototype that has no visible defects, just no new features.

**Checkpoint B (after Phase 2):** the recording is now protected against retakes and the Live Feed reads as real traffic. **This is where I recommend we re-evaluate.** If ≥ 2h remain before the deck must start, continue into Phase 3; otherwise stop and bank the time.

**Phase 4 is the designated drop.** Compliance export is genuinely valuable and it's the item I'd cut first — it's the only addition that doesn't appear on camera in the recommended demo arc (§8 of the audit), so it buys credibility with a reader of the repo rather than a viewer of the video.

---

## 4. Phase 1 — Credibility Fixes (2h 12m)

### 4.1 W1 — Executive Narrator: grounding guardrail + self-check *(P0 #1 — 40m)*

**The finding:** the Engineer-persona narrative invented `CustomerSupportAgent`, `ProductRecommendation`, and a `UserAuth` microservice migration. None exist. Our AI-governance product hallucinated, in the feature designed to explain hallucinations.

**Root cause, precisely.** Two compounding causes, both confirmed by reading the code:
- [`executive_narrator.py:30`](../backend/app/intelligence/executive_narrator.py#L30) — the only guardrail is *"Do not invent numbers beyond what's given."* It constrains numbers and nothing else. Names, causes, and remediations are unconstrained.
- [`executive_narrator.py:5-8`](../backend/app/intelligence/executive_narrator.py#L5-L8) — the engineer instruction demands *"be technical and specific: name flag types, **affected apps** … and **concrete pipeline fixes**."* But [`_collect_stats()`](../backend/app/api/routes_narrator.py#L18-L62) passes no app names, no root causes, and no remediation state. We ask for specificity the input cannot support — a textbook hallucination trigger. The CEO/CISO prompts ask for *tone*, not invented specifics, which is exactly why they stayed clean.

**Changes:**

1. **Give the model real nouns.** In `_collect_stats()`, add `monitored_app_names` (queried live from the `apps` table, so it can never drift from reality) and `known_flag_types`. The model can now reference true entities instead of manufacturing them.
2. **Round money at the source.** Change `round(total_impact, 2)` → `round(total_impact)` at [`routes_narrator.py:60`](../backend/app/api/routes_narrator.py#L60). *This also closes P2 #8 (`$740,358.75` cents-on-a-six-figure-estimate) for free* — one line, two findings.
3. **Rewrite the engineer instruction** to demand specificity *about the flags and apps provided*, and explicitly forbid naming services, microservices, pipelines, or internal systems not in the input.
4. **Harden the shared prompt guardrail** from "don't invent numbers" to: every proper noun, system name, root cause, and remediation must appear in the data above; where the data doesn't explain *why* something happened, say so rather than proposing a cause.
5. **Build `grounding_check(narrative, stats)`** — a *deterministic* validator (no second LLM; this must be auditable and free). It extracts candidate entities from the narrative — `CamelCase` tokens, `backticked` spans, `snake_case` identifiers — normalises them, and checks each against an allowlist assembled from the stats values plus a curated vocabulary of legitimate domain terms (GDPR, EU AI Act, TrustScore, RAG, PII, ControlPlane.ai…). Anything left over is an unsupported entity.
6. **Regenerate-once-then-fall-back.** If the check fails, regenerate a single time with the offending terms named in a corrective instruction. If it fails again, serve a deterministic template narrative built purely from stats. **The user can never be shown an ungrounded narrative** — worst case they see a plainer, provably-true one.
7. **Surface it in the UI.** The `/api/narrator` response gains a `grounding` object; the Impact page renders a badge beneath the narrative: *"✓ Grounding verified — 0 unsupported claims (deterministic check)"*, or, after a correction, *"Regenerated once — model introduced unsupported terms; corrected automatically."*

**Why this is worth 40 minutes and not 10.** The prompt-only fix makes the bug go away. *This* version turns the worst finding in the audit into the strongest single sentence in the demo: **"we apply our own Responsibility-layer discipline to our own LLM feature — and when our narrator drifts, our own guardrail catches it and says so on screen."** It is a live, honest demonstration of the product's entire thesis, and it is the kind of detail that separates a prototype from a product. It also pre-empts the exact question a technical judge would otherwise ask.

**Files:** `backend/app/intelligence/executive_narrator.py`, `backend/app/api/routes_narrator.py`, `frontend/app/impact/page.tsx`, `frontend/lib/api.ts`, `frontend/lib/types.ts`

**Acceptance:** 5 consecutive engineer-audience generations contain zero entities absent from the stats; the badge renders on all three tabs; the fallback path is exercised at least once by a forced test.

---

### 4.2 W2 — Global connectivity state + real error surfacing *(P0 #2, P1 #6 — 30m)*

**The finding:** killing the backend makes the whole dashboard degrade into a convincing, fully-styled, entirely empty product — `0.0` TrustScore, `$0` impact, "No active alerts" — with no on-screen hint that anything is wrong. Every caller ends in `.catch(console.error)`; the console is invisible on a recorded video.

**Changes:**

1. **Add a connection store** (`frontend/lib/connection.ts`) — a minimal module-level pub/sub with `markSuccess()` / `markFailure()` and a subscribe hook. No dependency, no context-provider churn.
2. **Instrument the API client at the single choke point.** [`request()` in `lib/api.ts`](../frontend/lib/api.ts#L16-L27) wraps its `fetch` in try/catch, reports success or failure to the store, and re-throws unchanged. **Every page gets connectivity awareness from one edit** — including pages I never open in this pass.
3. **`<ConnectionBanner />` in the app shell** — after 2 consecutive failures, a persistent amber pill: *"Backend unreachable — retrying automatically."* It clears on the first success. Because every page already polls on an interval, recovery is detected and reflected with no reload. A transient blip now reads as *"temporarily disconnected"* rather than *"this product has no data."*
4. **Sidebar status dot** — green `Live` / amber `Reconnecting`, so the healthy state is also visible. A status indicator that only ever appears when broken teaches viewers nothing about the normal case.
5. **Fix the confirmed defect in Try It Live's poll loop.** The `setInterval` callback at [`try-it/page.tsx:75-82`](../frontend/app/try-it/page.tsx#L75-L82) is `async` with **no try/catch** — if the backend dies mid-poll, `getInteraction` rejects unhandled every 1.5s and *the interval is never cleared.* That's a real leak regardless of the demo. Add error handling, an attempt cap that fires on failure as well as success, and a visible "evaluation unavailable" state.

> **Note on the audit's "stuck button" claim (P1 #6):** reading the code, `submit()` already has a `catch` that sets `error` and a `finally` that clears `sending` — so the stuck state I photographed may have been a 2-second screenshot timing artifact rather than a hang. **I will re-verify against a killed backend before changing that path**, and fix what actually reproduces. The unhandled-rejection leak above is confirmed by inspection and gets fixed either way.

**Files:** `frontend/lib/api.ts`, `frontend/lib/connection.ts` *(new)*, `frontend/components/ConnectionBanner.tsx` *(new)*, `frontend/app/layout.tsx`, `frontend/components/Sidebar` *(or wherever nav lives)*, `frontend/app/try-it/page.tsx`

**Acceptance:** kill the backend → banner appears within one poll cycle on *every* page; Try It Live shows a real error and a reset button; restart the backend → banner clears with no reload; no unhandled rejections in the console.

---

### 4.3 W3 — Trends: fix the garbled spend axis *(P0 #3 — 10m)*

**The finding:** the Daily AI Spend Y-axis renders `000075`, `00005` — the leading `0.` clipped off, because [`width={40}`](../frontend/app/trends/page.tsx#L86) can't fit Gemini's genuinely sub-cent per-call cost. The most visibly *broken-looking* thing in the product.

**Changes:** widen the axis to 64px, and add an **adaptive `tickFormatter`** — when the series max is under $0.01, render in cents (`0.75¢`) with the card subtitle noting the unit; otherwise render `$0.00`. Matching formatter on the tooltip. Sub-cent numbers aren't a bug in the data — Gemini really is that cheap, which is itself a good story — they're a bug in the *presentation* of the data, so I'm fixing the presentation rather than inflating the numbers.

I'll also sweep the other charts for the same too-narrow-axis pattern (`width={30}` appears on several) and widen any that can overflow.

**Files:** `frontend/app/trends/page.tsx`, plus any chart caught by the sweep

**Acceptance:** no clipped tick label at 1440px or 1920px, on any day-range and any app filter.

---

### 4.4 W4 — Loading & empty states everywhere *(P0 #4 — 25m)*

**The finding:** on first paint, before the API resolves, the Overview shows `AVG TRUSTSCORE 0.0` and `BUSINESS IMPACT AT RISK $0` — a confident, fully-styled, *wrong* headline number for up to two seconds of every page load. The panels below are blank with no indicator.

**Root cause:** `numericValue={summary?.avg_trust_score ?? 0}` at [`page.tsx:48`](../frontend/app/page.tsx#L48) collapses "not loaded" into "zero," and `useState<AlertItem[]>([])` at [`page.tsx:27`](../frontend/app/page.tsx#L27) makes "haven't fetched" indistinguishable from "genuinely none."

**Changes:**

1. **`StatCard` gains a `loading` prop** ([`ui.tsx:47`](../frontend/components/ui.tsx#L47)) — renders a pulsing skeleton bar in place of the number and dashes the sub-label. Fixed once, benefits every stat card in the app.
2. **Initialise list state as `null`, not `[]`**, so the three states — loading / empty / populated — are genuinely distinct. Skeleton rows while `null`; the real empty state only after a successful fetch returns nothing.
3. **Chart skeletons** for the TrustScore trend while `trends === null`, instead of an empty axis frame.
4. **Upgrade the empty copy to teach, not apologise** — per the audit's own cited research, and following the Review Queue's empty state, which the audit singles out as already best-practice. "No active alerts" becomes *"No active alerts — nothing crossed a threshold in the last hour."*

**Files:** `frontend/components/ui.tsx`, `frontend/app/page.tsx`, and the same pattern applied to `/live`, `/trends`, `/impact` stat regions

**Acceptance:** a hard refresh under throttled network shows skeletons throughout and **never** a `0.0` or `$0` that later changes.

---

### 4.5 W5 — Live Feed: stale selection + a demo-worthy default *(P1 #7, P1 from §3.2 — 12m)*

**Two findings, one file.**

1. **Stale cross-app selection** — changing the app filter leaves the previously-selected trace on screen, so the panel can show Customer Support Bot evidence while the dropdown reads Underwriting. Clear `selectedId` and `detail` in the filter's `onChange`. Straightforward.
2. **Boring cold open** — the default unfiltered feed leads with several unremarkable "allowed, 100" rows. Add a **"Flagged only"** toggle chip beside the app filter (default off, so nothing is hidden by default and the honest full-traffic view remains the baseline). Flipping it on gives an instantly demo-worthy list, and it's a genuinely useful control for a real operator triaging their day — not a demo prop.

**Files:** `frontend/app/live/page.tsx`

**Acceptance:** switching the filter clears the panel; the toggle produces a list where every visible row carries at least one flag.

---

### 4.6 W6 — Blocked interactions: "Threat Neutralized" treatment *(P2 #10 — 15m)*

**The finding:** a successfully-blocked jailbreak displays **TrustScore 90**, because the weighted formula only penalises Responsibility while Performance and Cost stay at 100. Mathematically defensible; reads as "pretty trustworthy" for an event that was an attack.

**Per your decision — presentation changes, scoring does not.** The formula is right: the score measures *our system's* behaviour, and our system behaved correctly by refusing to forward the request. Penalising ourselves for a successful defence would be wrong, and would shift every aggregate on the dashboard for cosmetic reasons.

**Changes:** in the trace detail panel, when `sync_action === "blocked"`, lead with a **`THREAT NEUTRALIZED — request never reached the model`** badge in place of the numeric ring, with the score demoted to a secondary line carrying a one-line explanation: *"TrustScore stays high because the control worked. The score measures the platform's response, not the attacker's intent."* Same treatment for `redacted` → **`PII AUTO-REDACTED`**.

This turns the audit's most confusing screen into one of the most self-explanatory, and it hands the demo a clean line to narrate.

**Files:** `frontend/app/live/page.tsx`, `frontend/components/ui.tsx`

**Acceptance:** the blocked trace leads with the badge; the explanation is legible without hovering.

---

### ▸ Checkpoint A — *every visible defect is fixed*

Re-run the Playwright audit script, confirm zero console errors, spot-check the six screenshots that originally showed defects. **If the clock has slipped, this is a clean, defensible place to stop.**

---

## 5. Phase 2 — Protect the Recording (50m)

### 5.1 W7 — Richer, non-repeating seed data *(P2 #9 — 25m)*

**The finding:** the Live Feed shows the same prompt verbatim 4+ times in a 7-row window ("Compare our Q2 churn drivers across the SMB and…"). ~15 scenario templates cycling with random timestamps. It quietly undercuts the "this is real production traffic" impression on the product's strongest screen.

**Changes:** expand to **40+ scenario templates** spread realistically across the three apps (support/refund/policy for the bot; codebase/HR-policy/architecture for the copilot; risk/underwriting/actuarial for the decision tool), and add light per-instance variation — substituting entities, regions, quarters, and figures — so no exact prompt repeats within a 20-row window. The distribution of clean vs. flagged cases stays as tuned, since the Policy Playground's precision/recall backtest depends on the labelled mix; **I'll re-run the playground after re-seeding to confirm its metrics still read sensibly.**

**Files:** `backend/app/seed/synthetic_apps.py`, `backend/app/seed/seed_data.py`

**Acceptance:** scroll 20 consecutive Live Feed rows — no verbatim duplicate prompt; Playground precision/recall/F1 remain in a sensible band.

---

### 5.2 W9 — Demo Mode *(25m — trimmed scope)*

**The problem it solves:** SLA windows are 30–120 seconds. During the audit the Review Queue emptied itself between screenshots. If a take needs a retry, the pending item is gone — and this is the one scene that *requires* live state.

**Trimmed to the high-value half.** Rather than a full mode-toggle with frozen timers threaded through the escalation engine, I'll build:

1. **`POST /api/demo/reset`** — re-seeds and guarantees two escalations in `pending` with an extended SLA deadline (10 minutes rather than 30–120 seconds), so a shot survives several retakes.
2. **A "Reset demo data" control** in the sidebar footer, rendered only when `NEXT_PUBLIC_DEMO_MODE=1`, so it cannot appear in a screenshot a judge might read as a fake-data button. Default off; the README documents it as a demo affordance, stated openly rather than hidden.

This is ~40% of the effort of the full Demo Mode for ~90% of the recording benefit. If we later want frozen timers, the endpoint is the foundation.

**Files:** `backend/app/api/routes_demo.py` *(new)*, `backend/app/main.py`, `frontend/components/Sidebar`, `.env.example`, `README.md`

**Acceptance:** click reset → Review Queue shows two pending items with multi-minute countdowns; approve/reject still works normally.

---

### ▸ Checkpoint B — *the recommended decision point*

Prototype has no visible defects, reads as real traffic, and the fragile scene is now retake-safe. **Decide here** whether the clock supports Phase 3, using the actual time rather than this morning's estimate.

---

## 6. Phase 3 — The Differentiator (50m)

### 6.1 W8 — Live pipeline visualisation on Try It Live

**Why this one is worth the most.** Our entire pitch is a **four-layer architecture** — Data Plane, Control Plane, Intelligence Layer, Presentation. Right now that architecture is *asserted* in the README and the deck, and invisible in the product: a user sees a response appear, then some scores appear. This makes the architecture **watchable**, which is the difference between a judge believing our diagram and a judge *seeing* it run.

**Design — six stages, driven by real signals:**

```
Ingress → Sync Guardrails → Model Call → Async Evaluation → TrustScore → Escalation
          (PII · blocklist   (Gemini)     (3 analyzers,       (weighted)   (tiered
           · budget)                       in parallel)                     decision)
```

Each stage carries a state — `pending` / `active` / `complete` / `blocked` — and shows its real latency where the backend reports one.

**The truthfulness rule (per §2, principle 4):** every stage *transition* is driven by real backend state. The sync response already returns `sync_action`, `sync_flags`, and `latency_ms`, which resolves stages 1–3 with genuine data. The existing 1.5s poll of `getInteraction(id)` resolves stages 4–6 the moment the evaluation row lands. The only illustrative element is the intra-stage shimmer while genuinely waiting — and the three analyzers really do run concurrently, so showing them fan out in parallel is accurate, not decorative. **No fabricated progress.** Building a fake progress bar into a governance product would be the same category of error as the narrator hallucination we're fixing in W1.

**The best beat in the demo:** submit the **Jailbreak** preset and the pipeline visibly **halts at Sync Guardrails**, with the Model Call stage greying out and labelled *"never called — request blocked in <10ms."* That single animation communicates more about why a pre-flight sync path matters than a paragraph of deck copy, and it pairs with W6's Threat Neutralized badge to make one coherent story.

**Files:** `frontend/components/PipelineFlow.tsx` *(new)*, `frontend/app/try-it/page.tsx`

**Acceptance:** clean prompt runs all six stages in order with real latencies; jailbreak preset halts at stage 2 with the model stage explicitly marked never-called; no stage advances without a corresponding backend signal.

---

## 7. Phase 4 — Stretch (30m)

### 7.1 W10 — Compliance audit export

**The rationale:** our market research found competitors underserve the "evidence pack for a regulator" workflow, and the audit's CISO persona explicitly needs an artifact they can forward. **This is also the designated cut** — it's the only addition that doesn't appear in the recommended demo arc, so it strengthens the repo for a reader more than the video for a viewer.

**Trimmed implementation — no PDF library:**
- **`GET /api/interactions/{id}/evidence`** → a structured evidence pack: prompt, raw vs. delivered response, every flag with its **detection method (rule vs. LLM judge)**, per-dimension scores, business impact, escalation decision, reviewer identity and rationale, and timestamps.
- **`GET /api/export/flagged.csv`** → the aggregate export for a period.
- **`/evidence/[id]`** — a print-optimised page that produces a clean PDF through the browser's own print dialog. No new dependency, no server-side rendering stack.

The detection-method column is the differentiating detail: it's the deterministic-vs-LLM split the Round 2 brief explicitly asks us to make visible, appearing in the artifact an auditor actually keeps.

**Files:** `backend/app/api/routes_export.py` *(new)*, `backend/app/main.py`, `frontend/app/evidence/[id]/page.tsx` *(new)*, `frontend/app/live/page.tsx`

**Acceptance:** exporting a flagged trace yields a file containing every element above; the print view fits one page.

---

## 8. Verification Protocol (20m)

Not "click around and see." The same method that produced the audit, so results are comparable:

1. **Production build** — `npm run build && npm run start`. Confirms the dev-mode error badge (P0 #5) cannot appear, *and* catches any type or build error that `next dev` tolerates. This is also the exact configuration we record against.
2. **Re-run the Playwright audit script** (`audit.js`) against the production build — all 7 pages, every control, same viewports (1440, 1920, 390). Compare against the original screenshots; every previously-defective shot must now be clean.
3. **Re-run the resilience test** (`resilience.js`) — kill the backend, confirm the banner appears everywhere, confirm Try It Live errors visibly, restart, confirm automatic recovery with no reload.
4. **Narrator grounding regression** — 5 generations per audience (15 total), asserting zero unsupported entities and a rendered badge on each.
5. **Console must be clean** — zero errors, zero unhandled rejections, across the full sweep.
6. **Seed integrity** — re-seed, confirm the Playground's precision/recall/F1 still land in a sensible band after the scenario expansion.

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Phase 3/4 squeeze the deck and video | **High** | **High** | The gated structure exists for exactly this. Checkpoint B is a real decision, not a formality. My recommendation is to stop after Phase 2 unless we're demonstrably ahead. |
| Grounding validator over-flags legitimate terms (false positives on "EU AI Act", "RAG") | Medium | Medium | Curated domain allowlist; regenerate-once before falling back; the deterministic template fallback is always safe, so worst case is a plainer narrative, never a broken page. |
| Gemini free-tier rate limits during verification (15 narrator generations) | Medium | Low | The narrator already uses the lighter judge model tier and a 90s response cache; I'll space the regression run and reuse cached results where the assertion allows. |
| Seed expansion perturbs Playground precision/recall | Low | Medium | Preserve the clean/flagged ratio; re-run and inspect the confusion matrix as an explicit acceptance criterion (§5.1). |
| A fix introduces a regression on a screen the audit called clean | Low | High | Full production-build sweep in §8 covers all 7 pages, not just the ones edited. |

---

## 10. What This Plan Explicitly Does *Not* Do

- **No mobile/responsive work** (audit P3) — previously agreed out of scope; desktop recording.
- **No changes to `trust_score.py` or the scoring math** — per decision #3.
- **No redesign of the visual system** — colours, typography, and motion were built and verified in the earlier Accenture-branding pass; the audit re-confirmed them.
- **No new pages beyond the print-only evidence view** — the audit found every existing page earns its place, and §7 of the audit found nothing to remove.
- **No demo video script or deck work** — separate deliverables, tracked separately, and the reason this plan is time-boxed.

---

## 11. Post-Plan Handoff

On completion, the following carry into the recording session:

1. **Record against the production build**, never `npm run dev` (P0 #5).
2. **Hit "Reset demo data" immediately before the Review Queue scene** — 10-minute SLA window, good for several takes.
3. **Follow the demo arc in §8 of the audit report** — with one amendment: the **Engineer narrator tab is no longer off-limits.** After W1 it becomes a feature to show deliberately, because the grounding badge is the proof point.
4. **Lead Try It Live with the Jailbreak preset** if W8 ships — the pipeline halting mid-flow is the strongest single visual in the product.
