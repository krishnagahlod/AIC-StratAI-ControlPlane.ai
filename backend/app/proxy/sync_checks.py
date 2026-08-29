import re
import time
from dataclasses import dataclass, field

from app.config import (
    BLOCKLIST_PATTERNS,
    DATA_LEAKAGE_PATTERNS,
    PII_PATTERNS,
    TOXICITY_QUICK_PATTERNS,
)

_PII_RE = {name: re.compile(pattern) for name, pattern in PII_PATTERNS.items()}
_LEAK_RE = {name: re.compile(pattern) for name, pattern in DATA_LEAKAGE_PATTERNS.items()}
_BLOCKLIST_RE = [re.compile(p, re.IGNORECASE) for p in BLOCKLIST_PATTERNS]
_TOXICITY_RE = [re.compile(p, re.IGNORECASE) for p in TOXICITY_QUICK_PATTERNS]

REDACTION_TOKEN = {
    "ssn": "***-**-****",
    "credit_card": "****-****-****-****",
    "email": "[redacted-email]",
    "phone": "[redacted-phone]",
    "api_key": "[redacted-secret]",
    "internal_url": "[redacted-internal-url]",
}


@dataclass
class SyncCheckResult:
    action: str  # allowed | redacted | blocked
    text: str
    flags: list[dict] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _redact(text: str, patterns: dict[str, re.Pattern]) -> tuple[str, list[dict]]:
    flags = []
    for name, pattern in patterns.items():
        matches = list(pattern.finditer(text))
        if not matches:
            continue
        text = pattern.sub(REDACTION_TOKEN.get(name, "[redacted]"), text)
        flags.append({"type": name, "count": len(matches)})
    return text, flags


def check_prompt(prompt: str) -> SyncCheckResult:
    start = time.perf_counter()
    for pattern in _BLOCKLIST_RE:
        if pattern.search(prompt):
            return SyncCheckResult(
                action="blocked",
                text=prompt,
                flags=[{"type": "prompt_injection", "pattern": pattern.pattern}],
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    redacted, pii_flags = _redact(prompt, _PII_RE)
    action = "redacted" if pii_flags else "allowed"
    flags = [{"type": "input_pii", "detail": f} for f in pii_flags]
    return SyncCheckResult(action=action, text=redacted, flags=flags, elapsed_ms=(time.perf_counter() - start) * 1000)


def check_response(response_text: str) -> SyncCheckResult:
    start = time.perf_counter()
    for pattern in _TOXICITY_RE:
        if pattern.search(response_text):
            return SyncCheckResult(
                action="blocked",
                text="This response was blocked by ControlPlane's real-time safety filter.",
                flags=[{"type": "toxicity_quick_block", "pattern": pattern.pattern}],
                elapsed_ms=(time.perf_counter() - start) * 1000,
            )

    redacted, pii_flags = _redact(response_text, _PII_RE)
    redacted, leak_flags = _redact(redacted, _LEAK_RE)
    all_flags = [{"type": "output_pii", "detail": f} for f in pii_flags] + [
        {"type": "data_leakage", "detail": f} for f in leak_flags
    ]
    action = "redacted" if all_flags else "allowed"
    return SyncCheckResult(action=action, text=redacted, flags=all_flags, elapsed_ms=(time.perf_counter() - start) * 1000)


class BudgetTracker:
    def __init__(self):
        self._spend: dict[int, float] = {}

    def record(self, app_id: int, cost_usd: float) -> None:
        self._spend[app_id] = self._spend.get(app_id, 0.0) + cost_usd

    def spend(self, app_id: int) -> float:
        return self._spend.get(app_id, 0.0)

    def is_over_budget(self, app_id: int, daily_budget_usd: float) -> bool:
        return self.spend(app_id) >= daily_budget_usd

    def budget_remaining_pct(self, app_id: int, daily_budget_usd: float) -> float:
        if daily_budget_usd <= 0:
            return 0.0
        remaining = max(daily_budget_usd - self.spend(app_id), 0.0)
        return round((remaining / daily_budget_usd) * 100, 1)


budget_tracker = BudgetTracker()
