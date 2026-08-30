# ControlPlane.ai
## Business Proposal — Round 2, Accenture Innovation Challenge 2026

**Prepared by:** Team StratAI — Krishna Gahlod, Mrunal Pachpande, Rudraksh Sharma (IIT Bombay)
**Track:** Problem Statement 1 — ControlPlane.ai
**Date:** August 30, 2026
**Companion artifacts:** [Working Prototype](README.md) · [Market Research Report](docs/market_research_report.md) · [Architecture Reference](docs/architecture_deep_dive.md)

---

## At a Glance

| | |
|---|---|
| **The problem** | Enterprises run generative AI across dozens of concurrent use cases and only discover failures — hallucinations, cost blowouts, bias, leaks — after a customer, regulator, or auditor already has. |
| **The market** | AI governance/observability is a Gartner-named category ("AI TRiSM"), growing 36-45% CAGR by every estimate, with $2.09B already priced into the top five pure-play vendors' valuations — and every one of them still fails at the same five things. |
| **The moment** | The EU AI Act's transparency clause went live August 2, 2026; Gartner forecasts 40%+ of agentic AI projects will be cancelled by 2027 for exactly the governance failure mode this product is built to prevent. |
| **The product** | A reverse-proxy oversight layer that scores every AI interaction on Performance, Cost, and Responsibility; converts flags into dollar business impact; routes decisions through confidence-tiered human escalation with an SLA; and lets teams backtest a policy against real traffic before deploying it. |
| **The proof** | Not a mockup. A working FastAPI + Next.js system, making real calls to Gemini, evaluated end-to-end, with the code and a clean-room-tested setup in the linked repo. |
| **The ask** | Advance ControlPlane.ai to the Grand Finale as the production-hardening track for enterprise AI trust infrastructure. |

---

## 1. Executive Summary

Every enterprise adopting generative AI is running the same experiment without a control group: deploy a chatbot, a copilot, an agent — and find out it hallucinated, leaked PII, or burned through a quarter's compute budget only when a customer complains, a regulator asks, or the invoice arrives. Our own research into this space (§3) puts a number on that experiment: **$67.4B in global hallucination-related losses**, **59% of enterprises watching their AI cost overruns get worse, not better**, and **1,313 documented court cases** where AI-generated content became a legal liability — all *before* accounting for the fact that Gartner expects **40% of enterprise applications to embed autonomous agents by the end of this year**, up from under 5% twelve months ago, introducing a materially larger and less predictable failure surface.

ControlPlane.ai is the control layer that sits between an enterprise's AI applications and the models they call, watching every request and response the way an SRE team watches production traffic — except the thing being monitored isn't uptime, it's trustworthiness. It scores every interaction across three dimensions the Round 2 brief itself names (Performance, Cost, Responsibility), translates the score into what it actually costs the business in dollars, and routes the response through a graduated decision — silently allow, flag for later review, escalate to a human with a countdown, or block — rather than the binary allow/block every competitor still ships.

We did not build a slide deck describing this. **We built it.** The repository linked to this proposal contains a working FastAPI backend making genuine calls to Google's Gemini API, a Next.js dashboard, and a policy backtesting tool that runs against 165 labeled historical interactions — verified end-to-end via a clean-room install test, not just a demo we've rehearsed. Section 4 walks through exactly what is real versus simulated, and why each of those calls was made deliberately, not as a shortcut.

This proposal makes the business case for why this is worth funding past the prototype stage: the market opportunity (§3), the product and its defensible differentiation (§4-6), the economics (§7), how we'd take it to market (§8), a phased plan to production (§9), and the risks we see clearly enough to have already started mitigating (§10).

---

## 2. The Problem, As Enterprises Actually Experience It

The Round 2 brief doesn't ask for a generic "AI safety" pitch — it names seven specific complexities that separate a real solution from a hackathon toy. We treat that list as a requirements document, not a suggestion, and we designed against every line of it:

| Real-world complexity (from the brief) | How ControlPlane.ai is designed against it |
|---|---|
| Different use cases (customer-facing vs. internal, real-time vs. batch) have different risk tolerance and latency budgets — one-size-fits-all doesn't work | Every monitored application has its **own** latency budget, risk tolerance, and TrustScore weighting (`weight_performance` / `weight_cost` / `weight_responsibility`) — a customer-facing bot and an internal copilot are governed by different math, not the same rulebook |
| Bias, hallucination, and privacy risks overlap — a fabricated detail about a person is both a hallucination *and* a privacy concern | Flags are dimension-tagged, not mutually exclusive; a single response can carry a `hallucination_llm_judge` flag *and* a `pii_leak` flag simultaneously, and the TrustScore and Business Impact Scorer both account for compounding flags rather than picking one category |
| No reliable real-time ground truth exists to verify a claim against | We say so explicitly in the product: every LLM-as-judge finding is tagged `verifiable: true/false` — when no source context is supplied, the system reports reduced confidence rather than pretending to have verified an unverifiable claim |
| Over-flagging causes alert fatigue and bypass; under-flagging creates liability — this tradeoff must be tuned, not solved away | This is precisely what the **Policy Playground** is for — it doesn't pick a threshold for you, it shows you the false-positive/false-negative tradeoff at every threshold against real historical data so *you* tune it deliberately |
| Multi-turn conversations and agents that act (not just generate text) compound risk | The Cost Analyzer's agent-loop detector already watches for compounding-risk patterns (repeated calls without convergence); full multi-turn conversation-state tracking is an explicit Phase 2 item (§9), not something we're claiming falsely to have solved in a hackathon prototype |
| Regulatory expectations differ by geography/industry and evolve — hard-coded rules age quickly | Detection *thresholds and weights* are configuration, not code — every app's policy is a data row, not a recompiled rule; this is the direct foundation for the policy-as-code layer on the roadmap |
| Enterprises consume models via API, not owned outright — can't inspect internals | ControlPlane.ai **never assumes model access below the API boundary.** Every check operates purely on the input prompt and output text, exactly matching how enterprises actually consume Gemini, GPT, or Claude |

**We are naming our own gaps on purpose.** A proposal that claims to have solved multi-turn agentic risk tracking in a hackathon prototype would not survive five minutes of technical due diligence from an Accenture reviewer. What we're presenting is a system that has correctly *identified* where the hard edges are, built real, working mechanisms for the parts that are tractable now, and sequenced the rest onto an honest roadmap.

---

## 3. Market Opportunity & Why Now

*(Full detail, methodology, and 40+ cited sources in [`docs/market_research_report.md`](docs/market_research_report.md); summarized here for the business case.)*

**The category is real, named, and funded.** Gartner has placed AI Security Platforms in its 2026 "Vanguard" tier of strategic technology trends under the umbrella of **AI TRiSM** (Trust, Risk and Security Management). Every credible market estimate — regardless of scope definition, which varies 5-10x by research house — converges on a **36-45% CAGR**. The five leading pure-play evaluation vendors (Arize, Fiddler, Galileo, Patronus, Openlayer) carry a **combined ~$2.09B valuation on ~$382M raised**, which is investors pricing in a market larger than today's revenue justifies — a classic early-category signal, not a mature, saturated one.

**The pain is quantified and compounding:**
- AI hallucinations cost businesses an estimated **$67.4B globally**; **1,313 documented court proceedings** worldwide have involved AI-generated content as of April 2026, and courts have explicitly rejected "the AI is a separate party" as a liability defense.
- **59% of organizations** report their wasted AI spend is *rising* year over year; the average enterprise AI budget went from **$1.2M (2024) to $7M (2026)**; audits of agentic workflows typically find **40-60% of inference is pure waste**.
- **Shadow AI** is now implicated in 43% of security incidents, more than double the prior year.

**The timing is not generic "AI is growing" framing — it is two specific, dated inflection points:**
1. **Regulatory:** The EU AI Act's Article 50 transparency obligations took effect **August 2, 2026** — four weeks before this proposal was written. The higher-stakes Annex III high-risk deadline was deferred to **December 2027**, which means enterprises have an 18-month window to build real governance infrastructure *now*, before the deadline that actually carries the €35M/7%-of-turnover penalty.
2. **Agentic:** Gartner projects **40% of enterprise applications will embed task-specific AI agents by the end of 2026**, up from under 5% a year earlier — and, in the same breath, predicts **over 40% of agentic AI projects will be cancelled by 2027** due to inadequate risk controls, explicitly warning that **"applying uniform governance across AI agents will lead to enterprise AI agent failure."** That is Gartner naming, almost verbatim, the exact problem ControlPlane.ai's per-app, confidence-tiered escalation model is built to solve.

**Who actually buys this** is a three-person committee — Chief AI Officer (champion), General Counsel/Chief Compliance Officer (**the actual economic buyer, budget owner**), and CISO (security risk owner). Every major competitor sells developer-first and bolts compliance reporting on later. ControlPlane.ai's Executive Narrator — plain-English reports for the CISO and the CEO, not just the engineer — is designed to sell directly to the buyer with the budget, from the first demo.

---

## 4. Solution Overview

### 4.1 What it is

ControlPlane.ai sits as a **drop-in reverse proxy** in front of an enterprise's AI applications — a one-line base-URL change, no code rewrite. For every request/response pair, it runs a four-layer pipeline:

```
Data Plane          → sub-10ms sync checks (PII redact, jailbreak blocklist, budget gate)
     ↓ (async, non-blocking)
Control Plane        → Performance / Cost / Responsibility analyzers, run in parallel
     ↓
Intelligence Layer   → TrustScore → Business Impact ($) → Smart Escalation (SLA-timed)
                        → Prescriptive Actions → Executive Narrator → Policy Playground
     ↓
Presentation Layer   → Live Feed, Trends, Business Impact/Exec Brief, Review Queue,
                        Policy Playground, Try-It-Live
```

Full technical detail is in [`docs/architecture_deep_dive.md`](docs/architecture_deep_dive.md) and the [README](README.md#2-architecture). The critical design decision — and the one a technical reviewer will probe first — is **which checks are deterministic and which use an LLM-as-judge, and why**:

| Check | Method | Why |
|---|---|---|
| PII, jailbreak blocklist, data-leakage | Deterministic regex | Must run on the synchronous path — sub-millisecond, not "fast for an LLM call" |
| Numeric-claim hallucination (a cited number absent from source context) | Deterministic (regex extraction + set comparison) | A quantitative claim should never depend on an LLM's own self-assessment |
| Faithfulness, contradiction, completeness, coherence | LLM-as-judge (Gemini) | No automated ground truth exists for open-ended claims — this is one of the brief's own sanctioned techniques, and every such flag is labeled `method: llm_judge` so it's never confused with a deterministic signal |
| Token cost, pricing, model-task-mismatch | Deterministic (real token counts × pricing table, rule-based complexity classifier) | Cost arithmetic must never be LLM-generated |
| Bias, toxicity, safety-policy violation | LLM-as-judge | Requires semantic understanding no regex can provide |
| Business Impact ($) | Deterministic formula over explicitly stated assumptions | A rule-based mapping table, not an LLM inventing a number |

This is not a stylistic choice — the Round 2 brief explicitly asks teams to justify when logic is deterministic versus LLM-based, and we treat that as a technical credibility test we intend to pass.

### 4.2 Target users and reference use cases

Matching the brief's own reference scenario, the prototype is seeded with three concurrent applications an enterprise would realistically run at once, each with **independently configured** risk tolerance and TrustScore weighting:

| Application | Type | Weighting emphasis | Why |
|---|---|---|---|
| **Customer Support Bot** | Customer-facing, real-time | Responsibility-weighted (35%) | Public-facing errors carry reputational and regulatory exposure |
| **Internal Knowledge Copilot** | Internal, mixed batch/real-time | Cost-weighted (40%) | Internal tools are the most common source of silent token waste |
| **Underwriting Decision-Support Tool** | Regulated, decision-support | Responsibility-weighted (55%) | Financial/insurance decisions carry the highest compliance and safety-violation stakes |

At the seeded volume (12,000 interactions/week/app across 3 apps = **36,000/week**), this directly matches the brief's own reference parameter of "tens of thousands of interactions per week across combined use cases."

### 4.3 Who inside the enterprise uses it

- **ML/Platform Engineers** — Live Feed & Trace Explorer, full evaluation traces down to individual flags and evidence
- **Compliance/Legal/CISO** — Executive Narrator's audience-specific reports, the audit trail behind every decision, and false-positive/negative reporting for regulatory conversations
- **Human reviewers** (support leads, underwriting supervisors) — the Review Queue, with full context and an SLA countdown, not a raw log dump
- **CEO/CTO** — a 60-second Executive Brief with the single biggest dollar risk and one recommended action, not a metrics dashboard

---

## 5. How We Address Every Solutioning Area in the Brief

| Brief's solutioning area | What's built, specifically |
|---|---|
| **Detection techniques** — rule-based heuristics, statistical anomaly detection, "AI-as-judge," retrieval verification, PII/entity detection | All five are implemented: regex/entity PII detection; rule-based redundant-call and agent-loop anomaly detection; Gemini as LLM-as-judge for faithfulness/bias/toxicity/safety; numeric retrieval verification against supplied source context |
| **Decision logic** — confidence scoring, tiered responses (allow/edit/flag/block), rules for pulling in a human | TrustScore (0-100, weighted per app) drives four tiers — Allow Silently, Allow + Flag Async, Escalate to Human (with Approve/Reject/**Edit**), Auto-Block + Alert — covering every response type the brief names, plus override rules (a critical safety violation always forces a block regardless of score; PII already auto-redacted doesn't also force an escalation) |
| **Architecture** — pre-response gate vs. inline middleware vs. post-hoc audit; parallel checks to protect latency | Hybrid by design: a **pre-response sync gate** (PII/jailbreak/budget, regex-based) protects latency, followed by a **post-hoc async audit** (the three analyzers run concurrently via `asyncio.gather`, never blocking the user-facing response) |
| **Governance** — configurable policy layer varying by use case/geography/risk appetite, with an audit trail | Per-app policy weights, risk tolerance, and latency budget are configuration rows, not code; every Interaction, Evaluation, Escalation, and human decision is persisted with full evidence — the audit trail an ISO 42001 or EU AI Act Annex III conformity assessment would require |
| **Feedback loops** — how flagged/overridden cases improve detection over time | Every reviewer decision (approve/reject/edit) is captured against the original flags today; automated threshold recalibration from that feedback is the first Phase 2 roadmap item (§9) — we show the mechanism working, not a claim it's already self-improving |
| **Metrics & monitoring** — false positive/negative rates, system trustworthiness reporting to a skeptical stakeholder | The **Policy Playground** *is* this requirement: it backtests any proposed TrustScore threshold against 165 labeled historical interactions and reports precision, recall, F1, and false-positive rate live — exactly the "report to a skeptical stakeholder" artifact the brief describes, not a marketing claim of accuracy |

---

## 6. Differentiation — What Every Competitor Still Doesn't Do

Our Round 1 competitive analysis identified five gaps across Fiddler, Galileo (Cisco), Confident AI, TrueFoundry, and Agent Control. We re-verified all five against 2026 funding and product data (§6 of the market research report) — every gap still holds, and two of them now have a named Gartner prediction attached:

| Gap | Competitors (2026) | ControlPlane.ai |
|---|---|---|
| Business impact translation | Raw metrics only (perplexity, toxicity score) | Dollar risk by category (Revenue/Compliance/Reputation/Customer Trust/Security/Operational), computed from stated assumptions |
| Confidence-tiered escalation | Binary block/allow, every platform | Four-tier graduated response with SLA-timed safe defaults — the direct answer to Gartner's "uniform governance causes agent failure" warning |
| Executive communication | Engineer-only dashboards | Persona-specific narratives (Engineer / CISO / CEO) from the same underlying data |
| Prescriptive action | Alerts, no fix | Root-cause → action → expected impact, rule-based first with an LLM fallback for novel patterns |
| Policy backtesting | Deploy guardrails blind | Full precision/recall/F1 backtest against historical, labeled traffic before a threshold ever ships |
| **Pricing model** *(new finding this round)* | Dominant per-seat pricing ($349/seat/mo in observed cases) that taxes cross-functional adoption | Base-platform-plus-usage, explicitly free of a per-seat tax — see §8 |

---

## 7. Business Case & Impact

### 7.1 The cost of the status quo (per enterprise, illustrative)

Using our own product's Business Impact Scorer assumptions — the same constants the working prototype uses, not new numbers invented for this document — applied at the brief's reference scale (three apps, ~36,000 interactions/week):

| Assumption | Value | Source |
|---|---|---|
| Average order value | $85 | `config.py: BUSINESS_ASSUMPTIONS` |
| Customer lifetime value | $620 | same |
| GDPR fine reference / probability per PII incident | $20M reference × 0.04% | same, calibrated conservatively against the EU AI Act's actual €35M/7%-of-turnover ceiling |
| Remediation cost per compliance incident | $1,500 | same |
| Weekly interactions per app | 12,000 | same — matches the brief's own "tens of thousands per week" parameter |

At even a **conservative 2-3% flagged-interaction rate** (well below the 5-15% general hallucination rate our research found, since flagged ≠ always harmful), an enterprise running this reference scenario is looking at:
- **Tens of thousands of dollars per week** in avoidable revenue, compliance, and reputational exposure surfaced *before* it becomes a customer complaint or a court filing — not after, which is the current default state per our research (§3).
- A cost-optimization signal on top: our own research found tiered model routing saves **87%** on a per-million-token basis versus routing everything to a frontier model. The Cost Analyzer's model-overuse detection is the mechanism that catches exactly this pattern.

### 7.2 Revenue model

Positioned deliberately against the dominant per-seat pricing pattern identified in our research (§3, §6):

- **Platform fee** (per monitored application, tiered by app criticality — customer-facing vs. internal vs. regulated) — covers the always-on proxy, dashboard, and audit trail.
- **Usage-based evaluation volume** — scales with actual interaction volume, not headcount, so Compliance, Legal, and Engineering can all use the product without a per-seat tax discouraging adoption.
- **Enterprise tier** — SSO, dedicated escalation SLAs, and compliance-pack exports (ISO 42001 / EU AI Act evidence bundles) for regulated industries.

This mirrors the "control-plane infrastructure as the moat" thesis our research surfaced: the model is commoditizing, the governance layer around it is where value concentrates.

### 7.3 Illustrative unit economics

At the benchmark our research found — **0.5-1% of AI budget for initial governance setup, 0.3-0.5% ongoing**, against a $7M average 2026 enterprise AI budget — a single mid-size enterprise account implies a **$21K-$70K/year** governance-tooling line item. A go-to-market targeting mid-market-to-enterprise accounts running 3+ concurrent AI use cases (the brief's own reference profile) gives a bottom-up path to a defensible SOM, rather than an unsupportable claim on a top-down multi-billion-dollar TAM.

---

## 8. Go-to-Market

1. **Land** with the Compliance/Legal economic buyer, not Engineering — the Executive Narrator is the first thing shown in a sales conversation, not the last.
2. **Prove** with a Policy Playground backtest against the prospect's own historical logs before asking them to change anything live — a zero-risk proof point competitors don't offer.
3. **Expand** from one flagship use case (typically the customer-facing app, highest visible risk) to the full portfolio of concurrent AI applications, using per-app configurability as the expansion mechanism rather than a re-sell.
4. **Anchor** enterprise deals on the compliance-evidence value (ISO 42001 / EU AI Act Annex III audit-trail export) given certification is moving from differentiator to procurement table stakes (§3).

Within an Accenture context specifically: this slots naturally alongside Accenture's own Responsible AI consulting practice and AI Refinery platform as the **monitoring and evidence layer** underneath client AI deployments Accenture is already building — a natural cross-sell into existing Responsible AI engagements rather than a competing product.

---

## 9. Phased Roadmap

| Phase | Scope | Status |
|---|---|---|
| **Round 1** (Aug 2026) | Concept validation, competitive positioning, pitch | ✅ Complete |
| **Round 2** (this submission) | Working prototype: full 4-layer pipeline, real Gemini integration, 7-page dashboard, clean-room-verified setup | ✅ Complete |
| **Phase 1 — Pilot hardening** (next 2-3 months) | Real message queue (Redis Streams) replacing in-process state; a fine-tuned/purpose-built classifier option alongside LLM-as-judge to cut latency and cost at scale; policy-as-code UI (a YAML/DSL editor) replacing config-file-level policy; automated threshold recalibration from captured reviewer feedback (closing the feedback loop named in §5 as a roadmap item) | Planned |
| **Phase 2 — Design partner deployment** (3-6 months) | Live pilot with a real enterprise's non-critical AI use case; multi-turn conversation-state tracking; ISO 42001 / EU AI Act evidence-bundle export | Planned |
| **Phase 3 — Grand Finale / production scale** | Multi-tenant auth, SOC 2 readiness, horizontal scaling of the evaluation layer, marketplace of pre-built policy templates by industry (finance, healthcare, insurance) | Planned |

This sequencing deliberately front-loads the infrastructure hardening (Phase 1) that a technical reviewer would otherwise flag as a gap between "hackathon prototype" and "production system" — see the honest limitations already documented in the [README](README.md#7-known-limitations--what-a-production-version-needs-next).

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **LLM-as-judge unreliability** — the judge model itself hallucinates or is rate-limited | Medium | Medium | Every judge call already degrades gracefully to "no signal from this check" rather than crashing the pipeline (built and tested, not theoretical); deterministic checks never depend on judge availability; Phase 1 adds a purpose-built classifier option to reduce judge dependency at scale |
| **Latency at production volume** — sync-path checks slow down under real load | Medium | High | Sync checks are regex-only by design, not LLM calls, keeping the sync path genuinely sub-10ms; async evaluation is fully decoupled and never blocks the user response |
| **Competitive response** — a funded incumbent (Fiddler, Galileo, Arize) ships business-impact translation or tiered escalation | Medium | Medium | These are architectural differentiators requiring a ground-up redesign of scoring and decision logic, not a feature toggle; our lead is in the underlying model, not a UI layer that's trivially copied |
| **Regulatory shift** — EU AI Act or India's framework changes requirements again | High (regulation is actively evolving, as the Aug 2026 Digital Omnibus deferral already showed) | Medium | Detection/decision logic is config-driven, not hard-coded, by design — exactly because the brief itself warns rigid rules age quickly |
| **Enterprise sales cycle length** — compliance/legal buyers move slowly | High | Medium | GTM leads with a zero-risk, no-integration-change Policy Playground backtest as the proof point, shortening the trust-building phase of the sales cycle |
| **False-positive fatigue** — over-flagging causes bypass, exactly the brief's own named risk | Medium | High | This is the entire reason the Policy Playground exists — it is the mitigation, not an afterthought |
| **Alert-fatigue on the human review queue at real volume** — the brief's own research finding ("teams planning for 10 escalations/day face 100") | Medium | High | Confidence-tiered escalation means only genuinely uncertain/critical cases reach a human at all; SLA-timed safe defaults prevent queue backlog from becoming silent failure |

---

## 11. Why StratAI

Team StratAI combines the two disciplines this problem actually needs in the same three people: hands-on AI/ML and full-stack engineering capability (evidenced by the working prototype itself — this was built, tested end-to-end including a clean-room install verification, and iterated based on real bugs found during that testing, not assembled from a template) and the market/business judgment to know that a governance tool nobody's compliance team will actually adopt is worthless regardless of its technical elegance. That combination — proven in this submission by having both a functioning system and a cited, sourced business case — is the basis for our ask to advance to the Grand Finale.

---

## Appendix

- **Live prototype & setup instructions:** [README.md](README.md)
- **Full architecture reference:** [docs/architecture_deep_dive.md](docs/architecture_deep_dive.md)
- **Full market research, methodology, and 40+ sources:** [docs/market_research_report.md](docs/market_research_report.md)
- **Original competitive analysis:** [docs/competitor_analysis.md](docs/competitor_analysis.md)
- **What's real vs. simplified in the prototype, and why:** [README.md §3](README.md#3-whats-real-whats-simplified--and-why)
