# Project Handover & Master Context: ControlPlane.ai (StratAI)

---

## 1. Executive Summary & Challenge Context

- **Competition:** Accenture Innovation Challenge (AIC) 2026
- **Theme:** AI Reinvention Made Real
- **Round:** Round 1 (Idea Submission & Video Pitch)
- **Team Name:** **StratAI**
- **Campus / Institution:** **IIT Bombay**
- **Team Members:**
  1. **Krishna Gahlod** (Team Leader) — B.Tech Chemical Engineering (Graduation: 2027)
  2. **Mrunal Pachpande** — B.Tech Civil Engineering (Graduation: 2027)
  3. **Rudraksh Sharma** — B.Tech Metallurgical Engineering (Graduation: 2027)

---

## 2. Problem Statement Selection & Analysis

### 2.1 The Chosen Problem
- **Track:** Problem Statement #1 — **ControlPlane.ai**
- **Core Problem Description:**
  Enterprises deploy generative AI & LLMs across hundreds of production use cases, yet they discover failures only *after* end-users or customers have already acted on them. AI models present three major continuous risks:
  1. **Performance Risk:** Hallucinations, factual fabrication, and "confidently wrong" assertions (~27% of enterprise LLM responses experience hallucination/accuracy drift).
  2. **Cost Risk:** Token-heavy runaway reasoning loops, unoptimized prompt chains, over-provisioning models for simple tasks (~40% of enterprise AI compute spend is wasted).
  3. **Responsibility / Safety Risk:** Accidental PII/PHI leakage, demographic bias, jailbreaks/prompt injections, and toxic outputs (regulatory exposure up to €20M under GDPR/EU AI Act).

### 2.2 Why This Over Other Tracks?
- **Track 1 (ControlPlane.ai)** has high enterprise urgency. Enterprise adoption of LLMs is bottlenecked by trust, governance, compliance, and unpredictability.
- While existing market tools function as purely developer/engineering trace dashboards, no existing platform translates AI governance into **quantified business impact ($ risk)** and **plain-English executive decision reports**.

---

## 3. Competitive Intelligence & Value Proposition Differentiation

### 3.1 Competitors Analyzed
1. **Fiddler AI:** Real-time LLM-as-a-judge observability, hallucination tracking, prompt injection guardrails.
2. **Galileo (Cisco):** Guardrails and metric evaluations for latency, toxicity, and hallucinations.
3. **Confident AI (DeepEval):** Unit-testing framework for LLMs and continuous telemetry.
4. **TrueFoundry:** Unified model routing, gateway proxy, and cost attribution.
5. **Agent Control:** Runtime agent loop interceptors.

### 3.2 Five Core Gaps Identified in Existing Solutions (StratAI Differentiators)
| Dimension | Existing Market Tools | StratAI (ControlPlane.ai) |
| :--- | :--- | :--- |
| **1. Business Impact Translation** | Displays raw technical metrics (e.g., perplexity, toxicity score 0.82) | Translates metrics into **$ financial risk**, customer volume exposed, and compliance penalties |
| **2. Executive Visibility** | Complex developer traces only useful for ML engineers | **Executive Narrator** auto-generates plain-English health & risk reports for CTOs, CISOs, and Boards |
| **3. Risk Escalation** | Rigid binary action (either hard block or silent pass) | **Smart Escalation**: Graduated response (`Allow` $\rightarrow$ `Flag` $\rightarrow$ `Escalate to Human Queue` with SLA $\rightarrow$ `Block`) |
| **4. Prescriptive Actionability** | "Alert: Hallucination spike detected" (no actionable fix) | Prescribes exact fixes with ROI (e.g., *"Enable 512-token chunking on Knowledge Base $\rightarrow$ cuts hallucination by 12%, saving \$34k/mo"*)|
| **5. Policy Playground** | Deploy guardrails blind and risk high false-positive rates | **Policy Backtesting**: Test guardrails against historical traffic logs before production rollout |

---

## 4. End-to-End System Architecture

ControlPlane.ai is structured into four distinct architectural layers with a strict latency budget.

```
[ AI Applications / Agents ]
            │
            ▼ (Incoming Requests)
┌─────────────────────────────────────────────────────────────┐
│ 1. DATA PLANE (High-Speed Reverse Proxy)                   │
│    - API Key & Auth Router                                  │
│    - Fast Sync Filters: PII Masking, Budget Check, Blocklist│
│    - Adds <10ms synchronous overhead                        │
└─────────────────────────────┬───────────────────────────────┘
                              │
            ┌─────────────────┴──────────────────┐
            ▼ (Async Intercept)                   ▼ (Forward Prompt)
┌───────────────────────────────┐        ┌────────────────────┐
│ 2. CONTROL PLANE (Analyzers)  │        │  Enterprise LLMs   │
│   • Performance: Hallucination│        │ (OpenAI, Anthropic,│
│   • Cost: Token & Loop Waste  │        │  Mistral, Gemini)  │
│   • Safety: PII, Bias, Jailbrk│        └─────────┬──────────┘
└───────────────┬───────────────┘                  │
                │                                  │ (Raw Output)
                ▼                                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. INTELLIGENCE LAYER (Core IP)                             │
│   • Dynamic TrustScore Engine (0–100 composite score)       │
│   • Business Impact Scorer (Quantifies $ and legal exposure)│
│   • Smart Escalation Router (Graduated threshold routing)   │
│   • Prescriptive Engine (Auto-recommends architectural fixes)
└───────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. PRESENTATION & WORKFLOW LAYER                            │
│   • ML Engineer Deep Trace & Observability Dashboard        │
│   • Human-in-the-Loop Review Queue (with SLA timer)         │
│   • Executive Narrator (CTO/CISO weekly board briefings)    │
│   • Policy Playground (Historical backtesting simulator)    │
└─────────────────────────────────────────────────────────────┘
```

### 4.1 Layer Deep-Dive
1. **Data Plane (Sync Proxy):**
   - Intercepts requests and responses as a drop-in gateway (compatible with OpenAI/Anthropic SDKs via base URL override).
   - Performs lightweight synchronous checks (regex/cache PII masking, token limits) to stay under **10ms latency budget**.
2. **Control Plane (Async Analyzers):**
   - Asynchronous worker queue evaluates complex tasks in the background (Hallucination detection via NLI/Context grounding, Semantic toxicity, Cost attribution by tenant).
3. **Intelligence Layer:**
   - **TrustScore Engine:** Computes a 0–100 score weighing Performance ($w_1$), Cost efficiency ($w_2$), and Responsibility ($w_3$).
   - **Business Impact Calculator:** Multiplies probability of error $\times$ transaction/deal value $\times$ regulatory multiplier.
4. **Presentation & Escalation:**
   - Routes critical uncertainty (TrustScore < threshold) to a Human-in-the-Loop review queue before final external commitment when configured in high-risk domains.

---

## 5. Artifacts and Project Files Produced

All project files are saved and validated in the workspace root `c:\StratAI\`:

| File Path | Description / Purpose |
| :--- | :--- |
| [StratAI_IITBombay_Final.pptx](file:///c:/StratAI/StratAI_IITBombay_Final.pptx) | **Official Presentation Submission.** Compliant with the Accenture PPT template. Contains Slide 1 (Cover), Slide 2 (Team Details), Slide 3 (Problem Statement with Risk Cards), Slide 4 (Solution & Native Flowchart Diagram), Slide 5 (Video Outline), and Slide 6 (Thank You). |
| [StratAI_IITBombay_Beautiful.pptx](file:///c:/StratAI/StratAI_IITBombay_Beautiful.pptx) | Alternative rich visual PPTX with card-based layouts and AI graphics. |
| [StratAI_IITBombay.html](file:///c:/StratAI/StratAI_IITBombay.html) | High-fidelity 3-slide web presentation (1280x720) styled in modern dark mode with Accenture purple accents. |
| [video_script.md](file:///c:/StratAI/video_script.md) | **1.5-minute Video Pitch Script** (~220 words) with scene breakdowns, visual cues, and delivery notes. |
| [AIC.md](file:///c:/StratAI/AIC.md) | Full competition documentation, schedule, rules, evaluation criteria, and guidelines. |
| [problem_statement_analysis.md](file:///C:/Users/krish/.gemini/antigravity-ide/brain/d1e2cbdd-2284-497c-880b-fcdb2e1f6b74/problem_statement_analysis.md) | Comprehensive breakdown of all 4 problem statements. |
| [competitor_analysis.md](file:///C:/Users/krish/.gemini/antigravity-ide/brain/d1e2cbdd-2284-497c-880b-fcdb2e1f6b74/competitor_analysis.md) | Detailed competitor mapping and differentiation strategy. |
| [architecture_deep_dive.md](file:///C:/Users/krish/.gemini/antigravity-ide/brain/d1e2cbdd-2284-497c-880b-fcdb2e1f6b74/architecture_deep_dive.md) | 17-node architectural breakdown, sequence diagrams, and latency budgets. |

---

## 6. Video Script Summary (Quick Reference)

- **Total Duration:** 90 seconds (1 min 30 sec)
- **Structure:**
  - **[0:00 - 0:15] The Hook & Problem:** Intro of Team StratAI (IIT Bombay), defining the 3 risks (Performance, Cost, Responsibility).
  - **[0:15 - 0:45] The Solution:** ControlPlane.ai as a high-speed reverse proxy (<10ms latency).
  - **[0:45 - 1:15] The Differentiator:** The Intelligence Layer, TrustScore (0-100), Business Impact ($ calculation), Human-in-the-loop Escalation, and Executive Narrator.
  - **[1:15 - 1:30] The Conclusion:** Moving enterprises from *"finding out later"* to *"finding it first."*

---

## 7. Roadmap for Technical Implementation (Next Phase / Prototype)

If you proceed to implement the codebase for ControlPlane.ai in subsequent rounds, here is the architectural scaffolding:

1. **Proxy Gateway (`FastAPI` / `Node.js / Express` / `Go`):**
   - Reverse proxy intercepting `POST /v1/chat/completions`.
   - Streaming token support with regex PII sanitizer.
2. **Evaluation & Analyzer Queue (`Celery` / `Redis` / `Temporal`):**
   - Asynchronous worker pool calculating groundedness, semantic similarity, and cost per request.
3. **Intelligence Engine:**
   - Python microservice that calculates TrustScore formula:
     $$\text{TrustScore} = 100 \times \left( w_{\text{perf}} \cdot S_{\text{perf}} + w_{\text{cost}} \cdot S_{\text{cost}} + w_{\text{resp}} \cdot S_{\text{resp}} \right)$$
   - Business Impact mapping matrix based on error type and transaction metadata.
4. **Web UI (`Next.js` / `React` + `TailwindCSS` / `Vanilla CSS`):**
   - **Executive View:** High-level narrative summaries with quarterly financial savings.
   - **Engineering View:** Trace explorer with latency, tokens, hallucination scores.
   - **Review Queue:** Human validation console for flagged completions.
   - **Policy Playground:** Historical replay engine.
