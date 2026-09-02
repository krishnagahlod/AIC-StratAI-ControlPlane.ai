# Sources and provenance

Every figure that appears in the README, the deck, or the running system, with where it came
from and how much weight it will bear.

The purpose of this file is narrow and deliberate: a reader should be able to check any number
we quote without taking our word for it, and should be able to see instantly which numbers are
**measured**, which are **cited**, and which are **our own assumptions**. Those three things
are not interchangeable, and a document that blurs them is doing something closer to marketing
than engineering.

## Confidence convention

| Level | Meaning |
|---|---|
| **Measured** | Produced by code in this repository, reproducible with a named command. |
| **Cited — high** | A primary source, or a figure reported consistently across several independent outlets. |
| **Cited — medium** | A single secondary source, or a projection. Directionally sound; the exact value would not survive scrutiny. |
| **Assumption** | Chosen by us to make a model work. Not a finding. Stated so it can be replaced. |

---

## 1. Measured — produced by this repository

These are the only numbers we generate ourselves, and none of them is transcribed by hand.

| Figure | Value | Command | Written to |
|---|---|---|---|
| Detection recall / precision / FPR | 1.000 / 0.881 / 0.188 | `python -m eval.report` | [`reports/evaluation.md`](../reports/evaluation.md) |
| Routing precision at every tier | 1.000 | `python -m eval.report` | [`reports/evaluation.md`](../reports/evaluation.md) |
| Problems detected but not routed | 59 of 96 | `python -m eval.report` | [`reports/evaluation.md`](../reports/evaluation.md) |
| Data Plane overhead, p50 / p99 | ~0.06 ms / < 0.25 ms | `python -m eval.bench_latency` | [`reports/latency.md`](../reports/latency.md) |
| Findings reached without an LLM | 94 of 157 (60%) | `python -m eval.report` | [`reports/evaluation.md`](../reports/evaluation.md) |
| Labelled corpus size | 165 interactions, 96 problems | `python -m eval.report` | [`reports/evaluation.md`](../reports/evaluation.md) |

Scope limits on these are stated in the reports themselves and are not repeated here.

---

## 2. Cited — external figures

Full context and the wider evidence base are in
[`market_research_report.md`](market_research_report.md), which carries 40+ cited sources. This
table lists only the figures that actually surface in the README, the deck, or the pitch.

| Figure | Used for | Source | Confidence |
|---|---|---|---|
| Shadow AI implicated in **43% of security incidents**, adding ~$670K to average breach cost | Problem framing | [IBM, via TechTimes (Jun 2026)](https://www.techtimes.com/articles/318438/20260615/shadow-ai-cybersecurity-risk-spikes-45-workers-use-unsanctioned-tools.htm) | Cited — high |
| **40–60% of inference is waste** in audited agentic workflows | Cost dimension | [Airia](https://airia.com/blog/how-to-identify-and-reduce-wasteful-ai-token-consumption-across-your-organization/) | Cited — medium |
| **59%** of organisations report wasted AI spend rising year over year | Cost dimension | [Flexera (2026)](https://www.flexera.com/blog/ai/ai-budgets-balloon-enterprise-lessons-flexera-2026/) | Cited — high |
| Enterprise AI budget **$1.2M (2024) → $7M (2026)** | Pricing basis | [Correlation One](https://www.correlation-one.com/blog/how-to-manage-ai-token-costs-in-the-enterprise-the-2026-playbook) | Cited — medium |
| Hallucinations cost businesses **$67.4B globally** | Problem framing | [Tendem](https://tendem.ai/blog/true-cost-ai-hallucinations-business-data) | Cited — medium |
| **GDPR ceiling €20M or 4%** of global turnover | Business-impact formula | GDPR Article 83(5) | Cited — high |
| EU AI Act penalties **€35M / 7%**, **€15M / 3%** | Regulatory framing | [Fello AI](https://felloai.com/eu-ai-act/) | Cited — high |
| EU AI Act **Article 50 live 2 Aug 2026**; Annex III deferred to **2 Dec 2027** | Regulatory timing | [Holland & Knight](https://www.hklaw.com/en/insights/publications/2026/04/us-companies-face-eu-ai-acts-possible-august-2026-compliance-deadline) · [Legiscope](https://www.legiscope.com/blog/eu-ai-act-timeline-deadlines.html) | Cited — high |
| AI governance market **36–45% CAGR** | Market sizing | Range across [Research and Markets](https://www.researchandmarkets.com/reports/5951966/ai-governance-market-report), [Grand View](https://www.grandviewresearch.com/industry-analysis/ai-governance-market-report), [MarketsandMarkets](https://www.globenewswire.com/news-release/2026/08/25/3350690/0/en/ai-governance-market-surges-to-5-78-billion-at-a-cagr-45-3-by-2029-report-by-marketsandmarkets.html) | Cited — medium |
| Total enterprise AI spend **$2.5T (2026)** | Macro context | [Gartner](https://www.gartner.com/en/newsroom/press-releases/2026-1-15-gartner-says-worldwide-ai-spending-will-total-2-point-5-trillion-dollars-in-2026) | Cited — high |
| India GCC ecosystem: **2,100+ centres, 2.3M+ professionals** | Market entry | [Nasscom-Zinnov via ORF](https://www.orfonline.org/research/capability-in-the-age-of-ai-india-s-gccs-and-the-future-of-white-collar-work) | Cited — high |
| Model pricing per 1K tokens | Cost analyzer | [Google AI pricing](https://ai.google.dev/pricing), encoded in `config.py: PRICING_TABLE` | Cited — high |

---

## 3. Assumptions — chosen by us

These are **not** research findings. They are the inputs that let the Business Impact Scorer
turn a flag into a dollar figure, and they live in one place —
`backend/app/config.py: BUSINESS_ASSUMPTIONS` — precisely so a reader can disagree with a value
and recompute rather than having to hunt through prose for a hardcoded number.

| Assumption | Value | Basis |
|---|---|---|
| Average order value | $85 | Representative mid-market e-commerce basket. Illustrative. |
| Customer lifetime value | $620 | Derived from the above at a typical repeat rate. Illustrative. |
| Weekly interactions per application | 12,000 | Chosen to match the brief's "tens of thousands per week" across three apps. |
| Churn probability per toxicity incident | 1.5% | Judgement. No public per-incident rate exists. |
| Probability of a fine per PII incident | 0.04% | Judgement. Deliberately conservative — most incidents are never fined. |
| Remediation cost per compliance incident | $1,500 | Judgement: analyst time, notification, log review. |
| Reputation incident base cost | $8,000 | Judgement. |

**The output of this model is an estimate, not an accounting figure.** It is useful because it
is consistent, traceable, and adjustable — the same finding always produces the same number,
and changing an assumption changes every downstream figure at once. It is not useful as a
forecast, and the README says so where the total is displayed.

---

## 4. Known caveats

Stated here rather than left for a reader to find.

- **Currency.** The business-impact formula uses **$20M** as the GDPR reference. The statutory
  ceiling is **€20M** or 4% of global turnover. We use the round figure in dollars for
  consistency with every other value in the model; at 2026 rates this understates the ceiling
  slightly. It is a reference constant in a probability-weighted estimate, not a currency
  conversion, and nothing downstream depends on the exchange rate.
- **The $67.4B hallucination cost is a 2024 figure**, still the most-cited baseline but no
  longer current. Quoted as an order of magnitude, not a live number.
- **Market-size estimates disagree by roughly 6x** depending on how the category is drawn.
  This is why we lead with the CAGR range (36–45%), where the sources converge, rather than any
  single absolute figure.
- **The dashboard's cumulative exposure total is demo-representative, not
  production-representative.** The seed mix over-indexes on failures by design. This is stated
  at the point of display in the README as well.
- **Percentages describing detector behaviour always come from `reports/`**, never from prose.
  If a figure in the README disagrees with the corresponding report, the report is correct and
  the README is stale.
