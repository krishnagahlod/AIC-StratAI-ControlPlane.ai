# ControlPlane.ai — Product Audit Report
## Senior PM / UX / AI-Engineering Review, Ahead of Demo Video Recording

**Date:** August 30, 2026
**Purpose:** A full walkthrough of the live product — every page, every control, every persona's journey — to find what's demo-ready, what needs a fix, and what's actively broken, before we record the prototype demo video.
**Method:** Not a code read-through. I ran the actual app (backend + frontend, freshly seeded), drove it end-to-end with an automated browser across every page and control (filters, sliders, tabs, presets, edge cases, a deliberately-killed backend to test failure behavior), captured ~30 screenshots of real states, and cross-checked what I found against current UX/AI-product research (cited throughout, not asserted from opinion).

---

## 0. Read This First — The One Finding That Changes Everything Else

**The Executive Narrator — our flagship differentiator, the feature whose entire premise is "translate AI risk into trustworthy language for executives" — hallucinates when generating the Engineer-audience report.**

Asked to summarize real flag data, it fabricated two service names that do not exist anywhere in our system (`CustomerSupportAgent`, `ProductRecommendation`), invented a root cause ("the model struggles to maintain context... leading to incorrect numerical comparisons"), invented a remediation already underway ("migrating a `UserAuth` microservice to a new, hardened version"), and stated all of it in the same confident, specific prose style as the true parts of the report. Screenshot evidence and full text: §3.4.

This is not a cosmetic bug. It is our own product committing the exact failure mode — a confident, specific, well-formatted fabrication — that ControlPlane.ai exists to catch in *other* products. If a technical judge notices it (and the Engineer persona is written for exactly the audience most likely to know those service names are fake), it doesn't just cost us one point on one screen — it invites the question "does your hallucination detector also hallucinate?" Root cause and fix are in §3.4 and §6. **This should be fixed before any other item on this list.**

---

## 1. Methodology & Sources

I evaluated the product against four disciplines, each grounded in current sources rather than personal taste:

- **AI product UX / trust design** — Nielsen Norman Group's 2026 findings that AI trust is *falling* even as adoption grows, that 63% of users trust AI more when it shows confidence/reasoning rather than black-box answers, and that consistent, predictable interaction increases trust by 47%. [Design Studio UI/UX](https://medium.com/@designstudiouiux/ux-design-for-ai-products-the-trust-problem-no-one-is-fixing-c48212558eb3), [UX Design Institute](https://www.uxdesigninstitute.com/blog/ux-design-principles-2026/)
- **Enterprise dashboard design** — the inverted-pyramid information hierarchy (headline KPIs first, detail on demand), F-pattern scanning behavior, and the "6-8 headline visuals per page, not 30" rule. [UXPin](https://www.uxpin.com/studio/blog/dashboard-design-principles/), [5of10](https://5of10.com/articles/dashboard-design-best-practices/)
- **Human-in-the-loop review UX** — confidence-based routing so reviewer queues stay focused on decisions that matter, contextual evidence over raw logs, and recorded reviewer rationale for audits. [Velt](https://velt.dev/blog/designing-human-in-the-loop-workflows-ai-products), [AufaitUX](https://www.aufaitux.com/blog/human-in-the-loop-ux/)
- **Loading/empty states & product trust** — "empty interfaces create confusion and mistrust; every interaction needs an immediate visible response," and empty states should teach, not just apologize. [UX Collective](https://uxdesign.cc/when-to-use-loaders-empty-states-ebd23cecc7d6), [Pencil & Paper](https://www.pencilandpaper.io/articles/empty-states)
- **B2B SaaS demo-video craft** — problem-first narrative structure, "show don't tell," value visible in the first 30 seconds. [Demopolish](https://demopolish.com/blog/saas-demo-video-best-practices/), [Komet Media](https://www.kometmedia.com/blogs/10-best-saas-product-demo-video-examples-for-2026-with-real-examples-you-can-watch)

---

## 2. User Personas & Journey Walkthrough

### 2.1 The ML/Platform Engineer — "is this response actually a problem?"
**Ideal flow:** land on Live Feed → filter to their app → click a flagged row → see evidence (raw vs. delivered, flags, scores) → understand *why* it fired → act.
**What works:** the trace detail panel is genuinely good — raw-vs-redacted output, per-dimension scores, flag chips tagged `rule` or `LLM judge`. This is the single strongest screen in the product for this persona.
**What breaks the flow:** the default (unfiltered, most-recent) feed frequently shows several boring, 95-100-score "allowed" rows before anything interesting — see §3.2. And switching the app filter doesn't clear a previously-selected trace from a *different* app, so the detail panel can show stale, mismatched context (§3.2).

### 2.2 The Compliance Officer / CISO — "can I trust this system, and can I prove it to a regulator?"
**Ideal flow:** land on Business Impact → switch to their persona tab → read a narrative they can forward to a board → check the audit trail exists.
**What works:** the CISO report is disciplined and grounded — it sticks to real numbers (§3.4). The category breakdown with dollar bars is exactly the artifact this persona needs.
**What breaks the flow:** the Engineer-tab hallucination (§0) sits one click away from the CISO's own tab — if they check both (compliance officers are professionally suspicious), they lose trust immediately. Also: dollar figures in the narrative carry cents (`$740,358.75`) — no CFO-facing report shows cents on a six-figure estimate; it reads as unpolished, not precise (§3.4).

### 2.3 The Human Reviewer — "do I approve, edit, or reject this, before the timer runs out?"
**Ideal flow:** land on Review Queue → see pending items with full context and a countdown → act.
**What works:** the empty state is genuinely good practice — it explains *why* it's empty and gives a next action ("send a live risky prompt from Try It Live"), matching the research's own recommendation (§1). The Approve/Reject/Edit three-way action beats every competitor's binary block/allow, confirmed still true in our market research.
**What breaks the flow:** the SLA windows (30s/120s) are so short that the *demo itself* is fragile — by the time I finished one round of screenshots, the queue was back to empty. This isn't a UX bug for real usage (it's the point — safe defaults apply fast), but it is a **demo-recording risk**: a pending item can expire mid-take. See §5 for the recommendation.

### 2.4 The CEO/CTO — "give me the one number and the one thing to do"
**Ideal flow:** land on Business Impact → CEO tab → read three sentences → done.
**What works:** the CEO narrative is exactly this — short, grounded, no jargon.
**What breaks the flow:** nothing specific to this persona beyond the shared cents-formatting issue above.

---

## 3. Page-by-Page Findings

### 3.1 Overview

**Working well:** clean information hierarchy (5 headline stats → trend chart → supporting panels), matches the inverted-pyramid best practice exactly. Animated numbers and the sliding nav indicator read as polished, not gimmicky.

**Needs improvement — P0, demo-visible:** On first paint (before the API calls resolve), every headline stat shows a real-looking but **wrong** value: `AVG TRUSTSCORE 0.0`, `BUSINESS IMPACT AT RISK $0`, and the Smart Alerts / Prescriptive Actions panels are blank with no loading indicator (screenshot: `01-overview-immediate.png`). This isn't a subtle timing issue — on a fresh page load or hard refresh during the video, the viewer's first impression of the product's flagship metric is **"$0 impact, 0 trust score"** for roughly half a second to two seconds, depending on network conditions. Per the loading-states research (§1): *"empty interfaces create confusion and mistrust — always provide visible feedback, even for short delays."* We are showing the opposite of feedback: a confident, fully-styled, wrong number.
*Fix direction:* render `—` (or a skeleton pulse) instead of `0`/`$0` for every stat card until its first real value arrives; never let "no data yet" and "the answer is zero" look identical.

**Needs improvement — P2:** at very wide viewports (1920px, a common recording resolution) the "Apps Under Management" panel has noticeably more empty vertical space than its neighboring chart card — minor, but visible if recorded at 1920×1080.

### 3.2 Live Feed & Trace Explorer

**Working well:** the trace detail panel (§2.1) is the best single screen in the product — raw vs. delivered response, per-dimension scores, evidence-backed flags, business impact narrative, escalation outcome, all in one place. This is the screen that should anchor the demo video.

**Needs improvement — P1:** the default, unfiltered view surfaces several unremarkable "allowed, 100" rows before anything demo-worthy (screenshot `03-live-default.png`). A viewer scrubbing to this page cold sees a boring list first. *Fix direction:* either default-sort/highlight flagged rows first, or script the demo to filter to a specific app immediately rather than showing "All Apps."

**Needs improvement — P1:** filtering by app does not clear a previously-selected trace from a *different* app — the detail panel can show "Customer Support Bot" evidence while the filter dropdown reads "Underwriting Decision-Support Tool" (screenshot `06-live-filtered-single-app.png`). Confusing on its own, and would look like a bug on camera if a viewer notices the mismatch. *Fix direction:* clear `selectedId`/`detail` when the app filter changes.

**Needs improvement — P2, content realism:** scrolling the feed repeats the *exact same prompt text* verbatim multiple times ("Compare our Q2 churn drivers across the SMB and..." appears 4+ times in a 7-row window). This is a direct consequence of only ~15 seed scenario templates cycling with random timestamps. It undercuts the "this is realistic production traffic" impression the demo depends on. *Fix direction:* either author more scenario variants or add light randomized text variation per repetition before recording.

**Noteworthy but not a bug — worth a script decision:** a blocked jailbreak attempt (a genuine security win — the attack was stopped) displays a TrustScore of **90**, because the weighted-average formula only dings the Responsibility dimension while Performance/Cost stay at 100 (screenshot `04-live-blocked-detail.png`). Mathematically defensible, but "TrustScore 90" reads as "pretty trustworthy" for an event that was literally an attack. A viewer without our formula in their head will find this counterintuitive. *Recommendation:* for `sync_action: blocked` interactions specifically, consider leading the UI with a "Threat Neutralized" badge rather than the numeric ring, or add a one-line tooltip explaining why a blocked attack still scores high (the block *worked*, which is the point).

### 3.3 Trends

**Working well:** splitting the old dual-axis chart into two single-axis charts (Interactions / AI Spend) was the right call — reads cleanly, no crossed scales.

**Broken — P0, visibly:** the "Daily AI Spend (USD)" Y-axis renders **truncated, garbled tick labels** — `000075`, `00005`, `000025` instead of `$0.000075`, `$0.00005`, `$0.000025` (screenshot `09-trends-single-app.png`). The leading `0.` is being clipped because the axis is only 40px wide, which isn't enough room for Gemini's genuinely tiny per-call cost at this scale. This is the single most visible outright rendering bug in the product — it looks broken on screen, not just imprecise. *Fix direction:* either widen the axis, format ticks in a friendlier unit (¢ or µ$), or pre-scale the series so the numbers aren't sub-cent to begin with.

### 3.4 Business Impact & Executive Brief

**Working well:** the CEO and CISO narratives are disciplined, grounded, and correctly persona-differentiated (formal/compliance-forward for CISO, plain-English/action-forward for CEO) — screenshots `11` and `13`.

**Broken — P0, credibility-critical:** the **Engineer** narrative fabricates specifics not present in the data it was given. Full text captured (screenshot `12-impact-engineer-loaded.png`):

> *"...these issues are most prevalent in the `CustomerSupportAgent` and `ProductRecommendation` services... To address this, we're prioritizing fine-tuning the retrieval-augmented generation (RAG) pipeline for both services... We also see `data_leakage` flags (9 instances), which are primarily originating from a specific, older version of our `UserAuth` microservice, and we are expediting its migration to the new, hardened version."*

None of `CustomerSupportAgent`, `ProductRecommendation`, or `UserAuth` exist anywhere in our system — our actual apps are `Customer Support Bot`, `Internal Knowledge Copilot`, and `Underwriting Decision-Support Tool`. The stats object passed to the LLM (`_collect_stats` in `routes_narrator.py`) contains only aggregate counts and a flag-type string — no service names, no root causes, no remediation status. The model invented all of it to satisfy the Engineer persona's prompt instruction to *"be technical and specific... name concrete pipeline fixes."*

*Root cause:* the prompt template's guardrail only says *"do not invent numbers beyond what's given"* — it never says don't invent facts, names, or causes. Asking for specificity the underlying data can't support is a known hallucination trigger, and the CISO/CEO prompts (which ask for tone, not invented specifics) don't exhibit the same failure — direct, isolated evidence the instruction wording is the cause, not the model or the data pipeline. *Fix direction:* explicitly forbid inventing system/service names or root causes not present in the input stats; ground "specific" in flag-type names and counts only, or literally list the actual monitored app names in the prompt so it has real nouns to reference instead of manufacturing them.

**Needs improvement — P2:** dollar figures in narratives carry two decimal places on six-figure numbers (`$740,358.75`) — the underlying `total_estimated_business_impact_usd` is `round(total_impact, 2)` in `routes_narrator.py`. No executive report shows cents on a $740K estimate. *Fix direction:* round to the nearest dollar (or nearest thousand) before it reaches the LLM's prompt.

### 3.5 Human Review Queue

**Working well:** the empty state explains itself and gives a next action — genuinely matches best practice rather than just being blank (screenshot `14`). The three-way Approve/Reject/Edit action beats every competitor's binary block/allow.

**Needs improvement — P1, demo-logistics not a code bug:** the 30-120 second SLA windows mean a "live pending item" demo shot has a short shelf life — if a take needs a retry, the item may have auto-defaulted by the next attempt. Not a defect (the short window is the intended design), but it needs a recording plan: see §5.

### 3.6 Policy Playground

**Working well:** no issues found. Slider, extremes (5/95), "Use recommended," and the confusion matrix all behaved correctly and looked polished across every state tested (screenshots `16-18`).

### 3.7 Try It Live

**Working well:** the preset buttons, grounded-vs-adversarial prompt examples, and the two-stage reveal (instant sync response, then async evaluation populating a few seconds later) is a genuinely strong "watch it work" moment when the backend is healthy.

**Broken — P0, resilience:** when the backend is unreachable, clicking **Send Request** leaves the button stuck showing **"Sending through proxy…"** with no visible error message to the user, even after the underlying fetch has failed (screenshot `27-backend-down-tryit-submit.png`; confirmed via console trace that the request genuinely failed with `ERR_CONNECTION_REFUSED`). There is no user-facing indication anything went wrong — just an indefinitely-spinning button. See §3.8 for the same failure mode across the whole app.

### 3.8 Cross-Cutting: Resilience & Failure Behavior

**Broken — P0, whole-app:** I deliberately killed the backend mid-session and reloaded the Overview page. The **entire dashboard silently degrades to a fully-populated-looking but completely empty/zero state** — `0.0` TrustScore, `$0` impact, an empty chart with just axis lines, "No active alerts," "No recommendations yet" (screenshot `26-backend-down-overview.png`) — with **zero indication anywhere in the UI that the backend is unreachable.** Every data-fetching call in the codebase ends in `.catch(console.error)`, which logs to the browser console (invisible to a normal viewer, and *definitely* invisible to a judge watching a recorded video) and nothing else. If the backend hiccups for any reason during the actual recording — a restart, a network blip, a Gemini rate-limit cascading into a timeout — the product will appear to have **no data at all**, indistinguishable from "this doesn't actually work," with no diagnostic on screen.
*Fix direction:* a lightweight global connectivity indicator (even a small "reconnecting…" toast or a persistent dot in the sidebar) the moment any core fetch fails, so a transient issue reads as "temporarily disconnected" instead of "broken."

**Operational, not a code bug — P0 for the recording session specifically:** the frontend dev server surfaces Next.js's built-in error-count badge (a small "N — 5 Issues" pill, bottom-left) whenever any console error occurs — visible in `26-backend-down-overview.png`. This is a **dev-mode-only** artifact. *Fix direction:* record the demo video against a production build (`npm run build && npm run start`), not `npm run dev`, so this indicator can never appear on camera regardless of what else happens during the take.

**Needs improvement — P3:** on a 390px-wide viewport the sidebar doesn't collapse, leaving ~134px of usable content width — confirmed already-known and out of scope per earlier agreed decision (the video will be recorded on desktop). Flagging only so it isn't rediscovered as a "new" bug later.

---

## 4. What's Working Well (don't touch these)

- The trace-detail panel's raw-vs-delivered / evidence-first design (§3.2) — this is the screen that sells the product.
- CISO and CEO Executive Narrator outputs (§3.4) — disciplined, grounded, correctly persona-differentiated.
- The Human Review Queue's empty state and three-way action set (§3.5).
- Policy Playground end-to-end (§3.6) — no issues found across any tested state.
- The Accenture-derived visual design system itself (colors, typography, motion) — out of scope for this audit since it was already deliberately built and verified in the prior redesign pass; nothing here changes that assessment.

## 5. What Needs to Be Added

1. **A loading/skeleton state for every stat card and chart** — replacing the "0/$0 flash" (§3.1) with something that reads as "loading," not "empty."
2. **A global connectivity indicator** for backend reachability (§3.8) — the single highest-leverage resilience fix given how badly a silent failure would read on camera.
3. **A demo-recording runbook step**: re-run the seed script immediately before recording the Review Queue scene, and know that the pending items expire within 30-120s — plan the shot list around that window rather than discovering it live (§2.3, §3.5).
4. **A guaranteed-outcome path for the "wow moment."** Because Try It Live makes a genuine, non-deterministic Gemini call, a live "watch it catch a hallucination" take could just... not hallucinate (we saw this ourselves in earlier testing — the "Hallucination bait" preset sometimes answers correctly). *Recommendation:* script the "it catches real problems" beat using the **pre-seeded Live Feed examples** (deterministic, guaranteed, and already excellent — §3.2), and use Try It Live to demonstrate *speed and mechanism* ("watch the full pipeline run in real time") on a preset likely to stay clean, rather than betting a one-take recording on an LLM behaving badly on cue.

## 6. What Needs to Be Fixed Before Recording (priority order)

| # | Finding | Section | Severity |
|---|---|---|---|
| 1 | Executive Narrator (Engineer persona) fabricates service names and root causes | §3.4 | **P0 — credibility-critical** |
| 2 | Whole-app silent failure on backend disconnect — zero on-screen indication | §3.8 | **P0 — demo-breaking if it occurs live** |
| 3 | Trends "Daily AI Spend" Y-axis renders garbled/truncated tick labels | §3.3 | **P0 — visibly broken on screen** |
| 4 | Overview stat cards flash `0`/`$0` before real data loads | §3.1 | **P0 — undercuts the headline metric on first paint** |
| 5 | Dev-mode error badge can appear on camera; record against a production build | §3.8 | **P0 — operational, trivial fix** |
| 6 | Try It Live: stuck loading state with no visible error on request failure | §3.7 | **P1** |
| 7 | Live Feed: app filter doesn't clear a stale cross-app selected trace | §3.2 | **P1** |
| 8 | Executive Narrator dollar figures show cents on six-figure estimates | §3.4 | **P2** |
| 9 | Live Feed content repetition (same seed scenario text verbatim, repeatedly) | §3.2 | **P2** |
| 10 | Blocked-jailbreak interactions show a counterintuitively high TrustScore | §3.2 | **P2 — needs a product decision, not just a fix** |

## 7. What Needs to Be Removed / Simplified

Nothing in the product needs outright removal — every page earned its place in the earlier audits and this one. The only "remove" is behavioral: **stop letting `.catch(console.error)` be the entire error-handling strategy** anywhere data is fetched (§3.8) — that pattern is what turns every one of the P0/P1 resilience findings into a silent failure instead of a visible, recoverable one.

---

## 8. Recommended Demo Narrative Arc (ties the findings together)

Per the demo-video research (§1) — problem-first, show-don't-tell, value visible in 30 seconds:

1. **Open on Live Feed**, pre-filtered to a specific app with a genuinely interesting flagged row already selected (not the default "All Apps" cold-open, per Finding #7/#9) — shows the trace-detail panel immediately, the product's strongest screen.
2. **Cut to Business Impact**, CEO tab first (grounded, punchy), then CISO tab (compliance-forward) — skip the Engineer tab entirely until Finding #1 is fixed.
3. **Cut to Policy Playground** — no known issues, drag the slider live, it's genuinely compelling and safe.
4. **Cut to Review Queue** with a freshly-seeded pending item (recording plan per Finding #3 in §5) — approve/reject it live.
5. **Close on Try It Live** with a preset chosen for reliability, narrating "the mechanism," not gambling on catching a live failure (Finding #4 in §5).

This sequencing leads with the two strongest, most bug-free screens (Live Feed trace detail, Policy Playground) and defers or works around every P0/P1 finding above rather than exposing them on camera.
