# ControlPlane.ai — Prototype Demo Video Script

**Deliverable:** Round 2 prototype demonstration, Accenture Innovation Challenge 2026
**Full runtime:** ~9 minutes · **Short cut:** ~3 minutes (scenes marked ★)
**Format:** Screen recording with voice-over. No talking head required.

> **On runtime:** I don't know the Round 2 video length cap. Every scene below is
> self-contained and timed, and the scenes that must survive a hard cut are marked **★**.
> Record the full walkthrough, then trim to whatever the limit turns out to be — the ★
> scenes alone tell a complete story in about three minutes.

---

## 0. Pre-flight runbook — do all of this before you hit record

Five minutes of setup that prevents every failure mode we found in testing.

| # | Step | Why |
|---|---|---|
| 1 | **Re-seed:** `cd backend && ./venv/Scripts/python -m app.seed.seed_data` | Clears any test traffic and restores a clean 165-interaction history |
| 2 | **Start the backend:** `uvicorn app.main:app --port 8000` | — |
| 3 | **Build and serve the frontend for production:** `npm run build && npm run start` | **Critical.** `npm run dev` renders an error-count badge bottom-left whenever any console error occurs. It will appear on camera |
| 4 | **Confirm `DEMO_MODE=1`** in `backend/.env` | Enables the "Arm review queue" control |
| 5 | **Click "Arm review queue"** in the sidebar, immediately before Scene 8 | Review items get a 10-minute SLA instead of 30–120s, so a retake can't lose the shot |
| 6 | **Warm the narrator:** open Business Impact and click through all three tabs once | Responses cache for 10 minutes, so Scene 7 won't wait on a live model call |
| 7 | **Check the sidebar reads "Backend connected"** (green dot) | Confirms the whole stack is live before you start |
| 8 | Browser at **1440×900**, zoom 100%, bookmarks bar hidden, notifications off | Consistent framing, nothing personal on screen |

**Two known conditions to route around, not fix on the day:**
- **"Critical Incidents" on the Overview will read 0.** It counts TrustScore < 30, and nothing in the seeded set scores that low. Don't point the cursor at it. The script never mentions it.
- **"Pending Human Reviews" reads 0 until you arm the queue.** Do step 5 before Scene 2, not just before Scene 8, so the Overview stat is non-zero when you first show it.

---

## Scene 1 ★ — Cold open: the problem *(0:00–0:35)*

**On screen:** Start on the **Live Feed**, already filtered with **"Flagged only"** on. Let the list sit still for three seconds before you speak. Do not open the app cold on an unfiltered list.

**Narration:**

> "Every enterprise deploying AI is running the same experiment without a control group. A model gives a confidently wrong answer, leaks a customer's details, or burns through a compute budget — and nobody finds out until a customer complains, a regulator asks, or the invoice arrives.
>
> This is ControlPlane.ai. It sits between an enterprise's AI applications and the models they call, and it scores every single interaction on three dimensions: is the answer right, what did it cost, and was it safe.
>
> What you're looking at is a running system. Real requests, real model calls, real evaluations."

**Why this beat:** Problem first, product second, proof third — and the proof is visible on screen within thirty seconds rather than promised.

---

## Scene 2 ★ — Fleet overview *(0:35–1:25)*

**On screen:** Click **Overview**. Move slowly across the five stat cards, then the trend chart, then **Apps Under Management**.

**Narration:**

> "The overview is the fleet-level picture. Across three monitored applications and the last fourteen days, we've evaluated a hundred and fifty-nine interactions at an average TrustScore of ninety-two.
>
> The second number is the one executives actually react to: **five hundred and ninety thousand dollars of estimated business exposure**. That is not a technical metric. Every flag this system raises gets converted into a dollar figure using documented assumptions — and I'll show you exactly where those come from later.
>
> On the right, the three applications we're monitoring. This is the important detail: each one is governed by **different maths**. The customer-facing support bot weights Responsibility at thirty-five percent. The internal copilot weights Cost at forty percent, because internal tools are where token waste hides. The underwriting tool weights Responsibility at fifty-five percent, because a bad decision there is a regulated event.
>
> One-size-fits-all governance is exactly what the brief warns against, and it's what Gartner predicts will cause enterprise agent programmes to fail. Every application here has its own policy."

**On-screen callout (post-production):** briefly highlight the three weightings as you say them.

---

## Scene 3 ★ — The trace: evidence, not a score *(1:25–2:40)*

**On screen:** Back to **Live Feed**. Click a row with a **hallucination** flag. Walk down the detail panel in order: prompt → source context → delivered response → sub-scores → flags.

**Narration:**

> "Here's where an engineer lives. Every interaction has a full trace.
>
> The prompt. The source document the model was supposed to be faithful to. And the response it actually gave.
>
> Underneath, the TrustScore breaks into its three components — Performance, Cost, Responsibility — each scored independently, then weighted by that application's own policy.
>
> Then the flags. And look at the tag on each one: **rule** or **LLM judge**. That distinction matters more than anything else on this screen.
>
> A numeric hallucination — a figure in the answer that appears nowhere in the source — is caught by a **deterministic rule**. Extract the numbers, compare the sets. It is reproducible and it never depends on a model's opinion of itself. PII detection, the jailbreak blocklist, and every cost calculation are deterministic for the same reason.
>
> Faithfulness, bias, toxicity — those need semantic judgement no regex can provide, so they use an LLM as judge. And we label them as judgements rather than measurements, because that's what they are.
>
> Across the current dataset that's forty-six deterministic findings, thirty-two rule-based, and sixty-six from LLM-as-judge. The brief asks teams to justify when logic is deterministic and when it's model-based. This is that justification, made visible on every single flag."

---

## Scene 4 ★ — A threat, neutralised *(2:40–3:20)*

**On screen:** In the same feed, click a row badged **blocked**.

**Narration:**

> "This one is a prompt injection attempt — someone trying to make the support bot reveal its system prompt.
>
> The banner says it plainly: **threat neutralised, the request never reached the model**.
>
> Now look at the TrustScore. It's high. That's deliberate, and it's worth explaining, because it looks wrong at a glance. The score measures **our platform's** response, not the attacker's intent — and our platform did exactly the right thing. It stopped the request in the synchronous path, before a single token was sent to the model. It cost nothing and it could not produce a harmful answer.
>
> Rather than hide that behind a number that looks confusing, the interface leads with the outcome in plain English and demotes the score to supporting evidence."

**Why this beat:** it pre-empts the single most likely "gotcha" question a sharp reviewer would ask, and turns it into a design decision you chose.

---

## Scene 5 — Redaction, and the audit trail *(3:20–4:10)*

**On screen:** Click a **redacted** row. Point at the delivered response, then the **raw model output** block below it. Then click **Evidence pack**.

**Narration:**

> "Redaction is the other intervention. Here the model put a customer's email and phone number into its answer. The user received a clean, redacted version — and we retain the raw output, in red, because an auditor needs to see what the model actually produced, not just what we let through.
>
> Which brings me to the artifact a compliance officer actually has to produce.
>
> *(click Evidence pack)*
>
> This is a per-interaction evidence pack. The interaction, the control applied, both versions of the response, every score with the policy weights that produced it, every finding with its detection method, the dollar estimate with its assumptions stated, and the governance decision including who decided what and when.
>
> It prints straight to PDF from the browser. There's also a CSV export of every finding across the period — currently a hundred and thirty-four rows — for when an auditor wants to sample rather than read.
>
> Our market research found this workflow is underserved across the whole competitive set. Everyone builds dashboards for engineers. Almost nobody builds the document the regulator asks for."

**On screen:** scroll the evidence page top to bottom once, slowly, then navigate back.

---

## Scene 6 — Trends: catching silent degradation *(4:10–4:45)*

**On screen:** Click **Trends**. Let the four-line chart settle. Change the range to 7 days, then back to 14. Then point at the two lower charts.

**Narration:**

> "Trends is how you catch drift — the failure mode where nothing breaks, quality just quietly erodes.
>
> TrustScore over time, with all three sub-dimensions plotted separately, so you can see *which* dimension is moving. A drop in Responsibility and a drop in Cost are completely different problems with completely different owners.
>
> Below: daily interaction volume, and daily spend. And I want to be honest about that spend axis — those are genuinely tiny numbers. Per-call inference at this volume costs fractions of a cent. The axis scales itself so day-over-day movement stays readable rather than collapsing to zero."

---

## Scene 7 ★ — The Executive Narrator, and a guardrail on ourselves *(4:45–6:00)*

**On screen:** Click **Business Impact**. Land on **CEO**, read it. Switch to **CISO**. Switch to **Engineer**. Then point at the green grounding badge. Then the category bars and the prescriptive actions list.

**Narration:**

> "Now the layer that separates this from an observability tool.
>
> The same underlying evaluation data, narrated for three different readers. The CEO version leads with the number and one recommended action. The CISO version is compliance-forward — redaction counts, regulatory framing, current posture. The engineer version names flag types and counts.
>
> Here's the part I'm most pleased with. This narrator is itself an LLM feature. So we hold it to the same standard we hold the applications we monitor.
>
> *(point at the badge)*
>
> **Grounding verified.** Every entity that narrative names is checked — deterministically, with no second model involved — against the data it was actually given. If the model introduces a service name or a root cause that isn't in the source data, the check catches it, the narrative is regenerated, and if it fails twice we serve a report built directly from the numbers instead.
>
> We built that because our own narrator hallucinated during testing. It invented two service names and a fake remediation story that existed nowhere in our system. Our own product, committing the exact failure it exists to catch. So we fixed it, and then we made the verdict visible on screen rather than quietly hoping.
>
> Below, the same dollars broken out by risk category — revenue, compliance, customer trust, reputation, security. And on the right, prescriptive actions: not just an alert, but a root cause, a specific fix, an expected value, and a confidence level. Seventy-five thousand dollars on a safety violation in the underwriting tool, with the exact guardrail to add."

**Why this beat:** it is the single most differentiating ninety seconds in the whole video. Do not cut it.

---

## Scene 8 ★ — Human in the loop, on a clock *(6:00–6:50)*

**On screen:** Click **Review Queue**. (Queue must be armed — runbook step 5.) Show the countdown ticking. Click **Edit & Approve** on one item, type a short edit, submit. Show it move to Recently Resolved.

**Narration:**

> "Every competitor ships binary block-or-allow. We ship four tiers.
>
> Below seventy, allow silently. Seventy to eighty-nine, allow but flag for asynchronous review. Thirty to sixty-nine, escalate to a human — and that's this queue. Under thirty, block outright and alert.
>
> These are the escalations that reached a human. Full context, the flags that triggered it, and a countdown — because a review queue without a deadline becomes a backlog, and a backlog becomes silent failure. When the timer expires, a safe default applies automatically and it's recorded as auto-defaulted.
>
> And the reviewer has three options, not two. Approve, reject, or — the one nobody else offers — **edit and approve**. Because most flagged responses aren't wrong, they're one sentence away from being right.
>
> *(make the edit, submit)*
>
> That decision is now captured against the original flags. Which is the foundation for automated threshold recalibration — the first item on our roadmap. We're showing you the mechanism working, not claiming the system already learns from it."

---

## Scene 9 ★ — Tune the tradeoff before you deploy it *(6:50–7:40)*

**On screen:** Click **Policy Playground**. Drag the slider slowly from 5 up to 95. Let the numbers and the confusion matrix recompute live. Click **Use recommended**.

**Narration:**

> "The brief names a tradeoff it says has to be tuned rather than solved: over-flag and you cause alert fatigue and people route around you; under-flag and you create liability.
>
> So we don't pick a threshold for you. We let you backtest one.
>
> This slider sets the TrustScore below which a response would be blocked. As I drag it, precision, recall, F1 and false-positive rate recompute live against a hundred and sixty-five **labelled** historical interactions.
>
> At seventy, precision is perfect but recall is nine percent — you'd catch almost nothing. At ninety-five, recall reaches seventy-eight percent with precision still at one hundred and a false-positive rate of zero. Push past that and you start blocking good responses.
>
> The confusion matrix underneath shows exactly what you'd be trading. This is the artifact you hand a sceptical stakeholder who asks how you know your guardrails work — a measurement, not a marketing claim.
>
> It's also our commercial wedge: a prospect can run this against their own historical logs before changing a single thing in production."

---

## Scene 10 ★ — Watch the architecture actually run *(7:40–8:40)*

**On screen:** Click **Try It Live**. Select the **Jailbreak attempt** preset. Click **Send Request**. Let the pipeline animate. Then run the **Grounded FAQ** preset and let the full pipeline complete.

**Narration:**

> "Everything so far was history. This is live.
>
> This is our four-layer architecture, drawn as a pipeline: ingress, synchronous guardrails, the model call, asynchronous evaluation, TrustScore, escalation.
>
> Let me send a jailbreak attempt through it.
>
> *(click Send Request)*
>
> Watch stage two. **Blocked — pattern matched.** And stage three: **model never called**. The request was stopped in the synchronous path, before any tokens were sent. The evaluation still runs, because a block is a governance event that belongs in the audit trail — but the model was never touched.
>
> Every stage there advances on a real signal from the backend. The proxy's response resolves the first three, including whether the model was called at all. The evaluation record resolves the rest. Nothing runs on a timer — building a fake progress bar into a governance product would be the same category of error we exist to catch.
>
> *(switch preset, send again)*
>
> And a clean request, end to end: guardrails pass, the model is called with real latency, three analyzers run in parallel, TrustScore resolves, and the escalation decision lands. That's a genuine call to Gemini, evaluated by the full pipeline, in a few seconds."

---

## Scene 11 ★ — Close *(8:40–9:10)*

**On screen:** Return to **Overview**. Let it sit.

**Narration:**

> "Four layers. A data plane that intercepts in under ten milliseconds. A control plane that evaluates on three dimensions in parallel. An intelligence layer that turns findings into dollars, decisions and plain English. And a presentation layer built for four different people, not just the engineer.
>
> This is a working system — the code is public, the setup is reproducible, and we've tested it from a clean clone.
>
> It is not production-ready, and we say so precisely: in-process state instead of a real message queue, no multi-turn conversation tracking yet, and a feedback loop we've built the capture for but not yet the recalibration. Those are the first three items on the roadmap, and we'd rather name them than have you find them.
>
> ControlPlane.ai. Team StratAI, IIT Bombay."

---

## The 3-minute cut

Keep only the **★** scenes and trim narration to the bolded claims:

| Scene | Trimmed to | Time |
|---|---|---|
| 1 Cold open | Problem + "this is a running system" | 0:00–0:25 |
| 2 Overview | The $590K number + per-app policy weights | 0:25–0:50 |
| 3 Trace | Rule vs LLM-judge on every flag | 0:50–1:20 |
| 4 Blocked | Threat neutralised, model never called | 1:20–1:35 |
| 7 Narrator | Three personas + grounding verified | 1:35–2:10 |
| 9 Playground | Slider, live precision/recall | 2:10–2:35 |
| 10 Try It Live | Jailbreak halts the pipeline | 2:35–2:55 |
| 11 Close | Four layers, public repo, named gaps | 2:55–3:05 |

---

## If something goes wrong mid-take

| Symptom | What's happening | Do this |
|---|---|---|
| Narratives look plain, badge says "Upstream LLM unavailable" | Both Gemini tiers hit their daily quota (free tier caps at **20 requests per day per model**) | The deterministic fallback is a real report — you can narrate it as designed graceful degradation. Or wait for the quota window and re-record Scene 7 only |
| Try It Live shows "the upstream model provider has hit its request quota" | Same cause, on the live proxy path | The proxy already retried the second model tier before showing this. Nothing to fix live — re-take later, or cut Scene 10's clean-request half and keep the jailbreak half, which never calls a model at all |
| A 429 / quota error right after changing the API key | The backend caches settings and builds its model client at import | **Restart the backend.** Also confirm you edited `controlplane-ai/backend/.env` — a stray `.env` at the repo parent is not read by anything |
| Amber "Backend unreachable" banner appears | Backend died | Stop. Restart it. The banner clears itself within one poll cycle — no reload needed. Re-take the scene |
| Review queue is empty | SLA expired | Click "Arm review queue", wait 2 seconds, re-take Scene 8 |
| Same prompt text appears repeatedly in the feed | You're on stale seed data | Re-seed. Current seed has 52 distinct prompts |

> **Quota budgeting for the shoot.** The free tier allows ~20 requests per day *per model*,
> and the proxy now spans two tiers. Scene 7 costs up to 3 calls (one per persona, then
> cached for 10 minutes) and Scene 10 costs 1–2. Warm the narrator once during setup and
> avoid re-running Try It Live more than a few times, and you will not come close to the cap.

---

## Post-production notes

- **Cursor:** move deliberately and pause on what you're describing. Never move while making a point.
- **Callouts:** add a soft highlight box for the per-app weights (Scene 2), the rule/LLM-judge tags (Scene 3), and the grounding badge (Scene 7). Nothing else needs annotation.
- **Pace:** roughly 150 words per minute. If a scene feels rushed, cut a sentence rather than speeding up.
- **Do not** add background music under the narration, or transition effects between scenes. Cut straight.
- **Record audio separately** from the screen capture if you can, then sync. It's far easier to re-take one sentence than one scene.
