import asyncio
import logging

from app.db.models import App, BusinessImpact, Escalation, Evaluation, Interaction, Recommendation
from app.db.session import SessionLocal
from app.evaluation import cost_analyzer, performance_analyzer, responsibility_analyzer
from app.intelligence import alerts, business_impact, escalation, prescriptive_actions, trust_score

logger = logging.getLogger("controlplane.evaluation")


def _run_evaluation_sync(interaction_id: int) -> None:
    db = SessionLocal()
    try:
        interaction = db.get(Interaction, interaction_id)
        if interaction is None:
            return
        app = db.get(App, interaction.app_id)

        perf_result = performance_analyzer.analyze(
            interaction.prompt,
            interaction.raw_response,
            interaction.rag_context,
            latency_ms=interaction.latency_ms,
            latency_budget_ms=app.latency_budget_ms,
        )
        cost_result = cost_analyzer.analyze(
            app.id, interaction.prompt, interaction.model, interaction.input_tokens, interaction.output_tokens, app.daily_budget_usd
        )
        resp_result = responsibility_analyzer.analyze(interaction.prompt, interaction.raw_response, interaction.sync_flags)

        all_flags = perf_result["flags"] + cost_result["flags"] + resp_result["flags"]
        trust = trust_score.compute(
            perf_result["score"], cost_result["score"], resp_result["score"],
            app.weight_performance, app.weight_cost, app.weight_responsibility,
        )
        risk_level = trust_score.risk_level_for(trust)

        evaluation = Evaluation(
            interaction_id=interaction.id,
            performance_score=perf_result["score"],
            cost_score=cost_result["score"],
            responsibility_score=resp_result["score"],
            trust_score=trust,
            risk_level=risk_level,
            response_cost_usd=cost_result["cost_usd"],
            flags=all_flags,
        )
        db.add(evaluation)

        cost_evidence = next((f.get("evidence", {}) for f in cost_result["flags"] if f["type"] == "model_overuse"), None)
        impact = business_impact.compute(app, all_flags, cost_evidence)
        db.add(
            BusinessImpact(
                interaction_id=interaction.id,
                risk_category=impact["risk_category"],
                estimated_impact_usd=impact["estimated_impact_usd"],
                affected_users=impact["affected_users"],
                confidence=impact["confidence"],
                narrative=impact["narrative"],
            )
        )

        decision_result = escalation.decide(trust, all_flags)
        db.add(escalation.build_escalation(interaction.id, decision_result["decision"]))

        if all_flags:
            alerts.register(db, app.id, interaction.id, risk_level, all_flags)

        recommendation = prescriptive_actions.generate_for_interaction(app, all_flags)
        if recommendation:
            db.add(
                Recommendation(
                    app_id=app.id,
                    priority=1 if any(f["severity"] == "critical" for f in all_flags) else 2,
                    issue=recommendation["issue"],
                    root_cause=recommendation["root_cause"],
                    action=recommendation["action"],
                    expected_impact=recommendation["expected_impact"],
                    estimated_value_usd=recommendation["estimated_value_usd"],
                    confidence=recommendation["confidence"],
                    method=recommendation["method"],
                )
            )

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Evaluation pipeline failed for interaction %s", interaction_id)
    finally:
        db.close()


async def evaluate_interaction(interaction_id: int) -> None:
    await asyncio.to_thread(_run_evaluation_sync, interaction_id)
