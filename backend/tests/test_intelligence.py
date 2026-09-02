"""Business impact, narrator grounding, and the evaluation maths.

The grounding tests matter most. That checker is what stops a generated executive summary
from inventing a system, a team, or a metric that does not exist, and a false positive
there is as damaging as a miss — it would discard a perfectly good narrative.
"""

import pytest

from app.intelligence import business_impact, grounding
from app.intelligence.policy_playground import _metrics_at_threshold
from eval.report import precision_at_prevalence


class _App:
    """Minimal stand-in; business_impact only reads these three attributes."""

    def __init__(self, name="Support Bot", app_type="customer_facing"):
        self.name = name
        self.app_type = app_type


def _flag(flag_type, severity="high", method="deterministic"):
    return {"type": flag_type, "severity": severity, "method": method}


class TestBusinessImpact:
    def test_a_clean_response_carries_no_cost(self):
        result = business_impact.compute(_App(), [])
        assert result["risk_category"] == "none"
        assert result["estimated_impact_usd"] == 0.0

    @pytest.mark.parametrize(
        "flag_type,expected_category",
        [
            ("pii_leak", "compliance"),
            ("safety_violation", "compliance"),
            ("bias", "reputation"),
            ("prompt_injection", "security"),
            ("semantic_contradiction", "revenue"),
            ("model_overuse", "operational_cost"),
            ("latency_budget_exceeded", "customer_trust"),
        ],
    )
    def test_flags_map_to_the_right_risk_category(self, flag_type, expected_category):
        result = business_impact.compute(_App(), [_flag(flag_type)])
        assert result["risk_category"] == expected_category

    def test_a_slow_response_is_a_trust_problem_not_a_cost_problem(self):
        """Regression: this used to fall through to the operational-cost default."""
        result = business_impact.compute(_App(), [_flag("latency_budget_exceeded")])
        assert result["risk_category"] == "customer_trust"

    def test_compliance_outranks_cost_when_both_are_present(self):
        result = business_impact.compute(
            _App(), [_flag("model_overuse", "critical"), _flag("pii_leak", "critical")]
        )
        assert result["risk_category"] == "compliance"

    def test_severity_drives_which_flag_leads(self):
        result = business_impact.compute(
            _App(), [_flag("model_overuse", "low"), _flag("bias", "critical")]
        )
        assert result["risk_category"] == "reputation"

    def test_a_deterministic_finding_is_reported_more_confidently_than_a_judgement(self):
        deterministic = business_impact.compute(_App(), [_flag("pii_leak", method="deterministic")])
        judged = business_impact.compute(_App(), [_flag("pii_leak", method="llm_judge")])
        assert deterministic["confidence"] > judged["confidence"]

    def test_every_impact_carries_a_narrative(self):
        result = business_impact.compute(_App(), [_flag("pii_leak")])
        assert result["narrative"].strip()


class TestNarratorGrounding:
    STATS = {"app_name": "Customer Support Bot", "trust_score": 87.4, "flag_count": 12}

    def test_a_faithful_narrative_passes(self):
        narrative = "Customer Support Bot held a trust score of 87.4 across 12 flags."
        assert grounding.check(narrative, self.STATS)["passed"]

    def test_an_invented_system_is_caught(self):
        narrative = "Trust dropped after the RiskHarmonizer service was enabled."
        result = grounding.check(narrative, self.STATS)
        assert not result["passed"]
        assert any("RiskHarmonizer" in term for term in result["unsupported_terms"])

    def test_a_sentence_opening_word_is_not_mistaken_for_a_proper_noun(self):
        """'Overall' only looks like a name because it starts the sentence."""
        assert grounding.check("Overall trust improved this week.", self.STATS)["passed"]

    def test_two_real_names_joined_by_and_are_not_read_as_one_invented_name(self):
        """Regression: the phrase pattern once spanned 'and', gluing two real names
        into a single phantom entity and failing a perfectly good narrative."""
        narrative = "Customer Support Bot and Underwriting Assistant both improved."
        stats = {"a": "Customer Support Bot", "b": "Underwriting Assistant"}
        assert grounding.check(narrative, stats)["passed"]

    def test_numbers_are_not_treated_as_entities(self):
        assert grounding.check("The score moved to 91.2 from 87.4.", self.STATS)["passed"]

    def test_the_verdict_reports_how_much_it_actually_checked(self):
        result = grounding.check("Customer Support Bot improved.", self.STATS)
        assert "checked_terms" in result and "unsupported_terms" in result


class TestThresholdMetrics:
    """The maths the Policy Playground and the evaluation report both depend on."""

    LABELLED = [(95.0, False), (92.0, False), (60.0, True), (20.0, True), (85.0, True)]

    def test_a_perfect_split_scores_perfectly(self):
        assert _metrics_at_threshold([(95.0, False), (20.0, True)], 90)["precision"] == 1.0
        assert _metrics_at_threshold([(95.0, False), (20.0, True)], 90)["recall"] == 1.0

    def test_raising_the_threshold_never_lowers_recall(self):
        recalls = [_metrics_at_threshold(self.LABELLED, t)["recall"] for t in range(10, 100, 10)]
        assert recalls == sorted(recalls)

    def test_confusion_counts_account_for_every_sample(self):
        m = _metrics_at_threshold(self.LABELLED, 90)
        assert m["true_positives"] + m["false_positives"] + m["false_negatives"] + m["true_negatives"] == len(self.LABELLED)

    def test_an_empty_corpus_does_not_divide_by_zero(self):
        m = _metrics_at_threshold([], 50)
        assert m["precision"] == 0.0 and m["recall"] == 0.0


class TestBaseRate:
    """The arithmetic behind the graduated-response argument."""

    def test_precision_falls_as_the_problem_becomes_rarer(self):
        at_ten = precision_at_prevalence(recall=1.0, fpr=0.19, prevalence=0.10)
        at_one = precision_at_prevalence(recall=1.0, fpr=0.19, prevalence=0.01)
        assert at_one < at_ten

    def test_a_perfect_detector_stays_perfect_at_any_prevalence(self):
        assert precision_at_prevalence(recall=1.0, fpr=0.0, prevalence=0.001) == 1.0

    def test_a_high_recall_detector_is_still_mostly_wrong_on_rare_events(self):
        """The finding the evaluation report is built on."""
        assert precision_at_prevalence(recall=1.0, fpr=0.19, prevalence=0.01) < 0.10

    def test_a_detector_that_never_fires_has_no_precision_rather_than_an_error(self):
        assert precision_at_prevalence(recall=0.0, fpr=0.0, prevalence=0.01) == 0.0
