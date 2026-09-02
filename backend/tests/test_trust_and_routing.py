"""TrustScore composition and the four-tier routing ladder.

These are the decisions with consequences — what gets blocked, what reaches a human — so
they are tested for behaviour rather than for implementation. Each test names the rule it
is protecting.
"""

import pytest

from app.config import ESCALATION_TIERS
from app.intelligence import escalation, trust_score


class TestTrustScore:
    def test_clean_response_scores_100(self):
        assert trust_score.compute(100, 100, 100, 0.4, 0.3, 0.3) == 100.0

    def test_weights_are_respected(self):
        """A dimension carrying more weight moves the composite further."""
        perf_heavy = trust_score.compute(0, 100, 100, 0.8, 0.1, 0.1)
        resp_heavy = trust_score.compute(0, 100, 100, 0.1, 0.1, 0.8)
        assert perf_heavy < resp_heavy

    def test_weights_need_not_be_normalised(self):
        assert trust_score.compute(60, 90, 30, 1, 1, 1) == trust_score.compute(60, 90, 30, 2, 2, 2)

    def test_zero_weights_fall_back_to_equal_rather_than_dividing_by_zero(self):
        assert trust_score.compute(60, 90, 30, 0, 0, 0) == pytest.approx(60.0)

    def test_score_is_clamped_to_range(self):
        assert trust_score.compute(-500, -500, -500, 0.4, 0.3, 0.3) == 0.0
        assert trust_score.compute(500, 500, 500, 0.4, 0.3, 0.3) == 100.0

    @pytest.mark.parametrize(
        "score,expected",
        [(100, "minimal"), (90, "minimal"), (89.9, "low"), (70, "low"),
         (69.9, "moderate"), (30, "moderate"), (29.9, "critical"), (0, "critical")],
    )
    def test_risk_bands_match_their_boundaries(self, score, expected):
        assert trust_score.risk_level_for(score) == expected


class TestEscalationTiers:
    """The ladder itself. A gap or an overlap here would silently misroute traffic."""

    def test_tiers_cover_zero_to_one_hundred_without_gaps(self):
        ordered = sorted(ESCALATION_TIERS, key=lambda t: t["min"])
        assert ordered[0]["min"] == 0
        assert ordered[-1]["max"] == 100
        for lower, upper in zip(ordered, ordered[1:]):
            assert upper["min"] == lower["max"] + 1, "tier boundaries must be contiguous"

    @pytest.mark.parametrize(
        "score,expected",
        [(100, "allow_silent"), (90, "allow_silent"),
         (89, "allow_flag_async"), (70, "allow_flag_async"),
         (69, "escalate_human"), (30, "escalate_human"),
         (29, "auto_block_alert"), (0, "auto_block_alert")],
    )
    def test_score_maps_to_the_expected_tier(self, score, expected):
        assert escalation.decide(score, [])["decision"] == expected


class TestEscalationOverrides:
    """The two rules that deliberately disagree with the score."""

    def test_critical_safety_violation_forces_a_block_from_any_score(self):
        flags = [{"type": "safety_violation", "severity": "critical"}]
        result = escalation.decide(98.0, flags)
        assert result["decision"] == "auto_block_alert"
        assert result["override_applied"] == "critical_safety_violation_forced_block"

    def test_non_critical_safety_violation_does_not_force_a_block(self):
        flags = [{"type": "safety_violation", "severity": "high"}]
        assert escalation.decide(98.0, flags)["decision"] == "allow_silent"

    def test_pii_already_redacted_is_not_worth_a_humans_time(self):
        """PII is redacted synchronously, so the leak never reached anyone.

        Escalating it would spend a reviewer on an issue already resolved.
        """
        result = escalation.decide(45.0, [{"type": "pii_leak", "severity": "high"}])
        assert result["decision"] == "allow_flag_async"
        assert result["override_applied"] == "pii_already_auto_redacted_no_other_issue"

    def test_pii_alongside_another_issue_still_escalates(self):
        """The downgrade must not become a way to smuggle a real problem past review."""
        flags = [
            {"type": "pii_leak", "severity": "high"},
            {"type": "semantic_contradiction", "severity": "high"},
        ]
        result = escalation.decide(45.0, flags)
        assert result["decision"] == "escalate_human"
        assert result["override_applied"] is None

    def test_no_override_is_recorded_when_none_was_applied(self):
        assert escalation.decide(95.0, [])["override_applied"] is None


class TestEscalationRecords:
    def test_human_review_gets_a_pending_status_and_an_sla(self):
        record = escalation.build_escalation(1, "escalate_human")
        assert record.status == "pending"
        assert record.sla_deadline is not None

    def test_a_block_gets_the_tighter_critical_sla(self):
        blocked = escalation.build_escalation(1, "auto_block_alert")
        reviewed = escalation.build_escalation(2, "escalate_human")
        assert blocked.sla_seconds < reviewed.sla_seconds

    def test_allowed_traffic_creates_no_review_burden(self):
        for decision in ("allow_silent", "allow_flag_async"):
            record = escalation.build_escalation(1, decision)
            assert record.status == "resolved"
            assert record.sla_deadline is None
