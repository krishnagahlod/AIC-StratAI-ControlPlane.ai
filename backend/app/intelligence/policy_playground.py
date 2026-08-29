from sqlalchemy import select

from app.db.models import Evaluation, Interaction


def _labeled_scores(db, app_id: int | None) -> list[tuple[float, bool]]:
    query = select(Evaluation.trust_score, Evaluation.ground_truth_is_problem).where(
        Evaluation.ground_truth_is_problem.isnot(None)
    )
    if app_id is not None:
        query = query.join(Interaction, Interaction.id == Evaluation.interaction_id).where(
            Interaction.app_id == app_id
        )
    return [(row[0], bool(row[1])) for row in db.execute(query).all()]


def _metrics_at_threshold(labeled: list[tuple[float, bool]], threshold: float) -> dict:
    tp = fp = fn = tn = 0
    for score, is_problem in labeled:
        would_block = score < threshold
        if would_block and is_problem:
            tp += 1
        elif would_block and not is_problem:
            fp += 1
        elif not would_block and is_problem:
            fn += 1
        else:
            tn += 1

    total = len(labeled)
    blocked = tp + fp
    precision = tp / blocked if blocked else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "threshold": threshold,
        "total_labeled": total,
        "would_block": blocked,
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "false_positive_rate": round(fpr, 3),
        "f1": round(f1, 3),
    }


def simulate(db, threshold: float, app_id: int | None = None) -> dict:
    labeled = _labeled_scores(db, app_id)
    return _metrics_at_threshold(labeled, threshold)


def recommend_threshold(db, app_id: int | None = None) -> dict:
    labeled = _labeled_scores(db, app_id)
    candidates = [_metrics_at_threshold(labeled, t) for t in range(5, 100, 5)]
    if not candidates:
        return {"recommended_threshold": 30, "reason": "No labeled historical data available yet.", "candidates": []}

    best = max(candidates, key=lambda m: (m["f1"], -m["threshold"]))
    return {
        "recommended_threshold": best["threshold"],
        "reason": f"Maximizes F1 ({best['f1']}) across {best['total_labeled']} labeled historical interactions.",
        "candidates": candidates,
    }
