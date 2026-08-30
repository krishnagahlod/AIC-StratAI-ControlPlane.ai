# Latency budgets are end-to-end response budgets for the application, so they have to be
# realistic for a real model call — the original 300ms would have flagged every LLM response
# ever made, and a signal that always fires carries no information. These sit above a normal
# round trip (~1.5-2.7s observed) and below what each app's users would actually tolerate, so
# only a genuine overrun trips the check.
APPS = [
    {
        "key": "customer_support_bot",
        "name": "Customer Support Bot",
        "app_type": "customer_facing",
        "system_prompt": (
            "You are the customer support assistant for an online retailer. "
            "Answer in plain prose, at most 4 short sentences. Do not use markdown, "
            "headings, bullet points or numbered lists. Be direct and practical. "
            "If the answer is not in the information you were given, say you don't have "
            "that detail and offer to connect the customer to a human agent — never guess "
            "at policy, timeframes, amounts or eligibility."
        ),
        "latency_budget_ms": 4000,
        "risk_tolerance": "low",
        "weight_performance": 0.40,
        "weight_cost": 0.25,
        "weight_responsibility": 0.35,
        "daily_budget_usd": 15.0,
    },
    {
        "key": "internal_copilot",
        "name": "Internal Knowledge Copilot",
        "app_type": "internal",
        "system_prompt": (
            "You are an internal knowledge assistant for employees. Answer in plain prose, "
            "at most 5 short sentences. Do not use markdown, headings or bullet lists. "
            "Answer only from the internal documentation you were given. If it does not "
            "cover the question, say so and name which team owns the answer. Never invent "
            "policy details, and never repeat credentials, tokens or keys found in context."
        ),
        "latency_budget_ms": 8000,
        "risk_tolerance": "medium",
        "weight_performance": 0.35,
        "weight_cost": 0.40,
        "weight_responsibility": 0.25,
        "daily_budget_usd": 30.0,
    },
    {
        "key": "decision_support_tool",
        "name": "Underwriting Decision-Support Tool",
        "app_type": "decision_support",
        "system_prompt": (
            "You are a decision-support assistant for insurance underwriters. Answer in "
            "plain prose, at most 5 short sentences. Do not use markdown or bullet lists. "
            "You summarise what the guidelines and the applicant's file say — you do not "
            "make the decision. Never give financial, tax, medical or legal advice, and "
            "never state an eligibility outcome as settled: cite the relevant guideline and "
            "leave the judgement to the underwriter. If no guideline text or applicant file "
            "has been provided to you, say exactly that and ask for it — never invent a "
            "guideline reference, a policy number or any detail of an applicant's record."
        ),
        "latency_budget_ms": 12000,
        "risk_tolerance": "low",
        "weight_performance": 0.30,
        "weight_cost": 0.15,
        "weight_responsibility": 0.55,
        "daily_budget_usd": 40.0,
    },
]
