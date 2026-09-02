"""Read the labelled corpus out of the database.

Every seeded interaction carries a ground-truth label recorded at authoring time, before
any analyzer ran on it (`seed_data.py`). That is what makes precision and recall
meaningful here: the label is independent of the score it is used to judge.
"""

from sqlalchemy import select

from app.db.models import App, Evaluation, Interaction


def labeled_scores(db, app_id: int | None = None) -> list[tuple[float, bool]]:
    """(trust_score, is_problem) for every labelled interaction."""
    query = select(Evaluation.trust_score, Evaluation.ground_truth_is_problem).where(
        Evaluation.ground_truth_is_problem.isnot(None)
    )
    if app_id is not None:
        query = query.join(Interaction, Interaction.id == Evaluation.interaction_id).where(
            Interaction.app_id == app_id
        )
    return [(row[0], bool(row[1])) for row in db.execute(query).all()]


def label_counts(db) -> list[tuple[str, bool, int]]:
    """(label, is_problem, count), most frequent first."""
    rows = db.execute(
        select(Evaluation.ground_truth_label, Evaluation.ground_truth_is_problem)
        .where(Evaluation.ground_truth_label.isnot(None))
    ).all()
    tally: dict[tuple[str, bool], int] = {}
    for label, is_problem in rows:
        key = (label, bool(is_problem))
        tally[key] = tally.get(key, 0) + 1
    return sorted(((k[0], k[1], v) for k, v in tally.items()), key=lambda r: -r[2])


def per_app(db) -> list[tuple[str, int, int]]:
    """(app name, labelled count, problem count) for each monitored application."""
    rows = db.execute(
        select(App.name, Evaluation.ground_truth_is_problem)
        .join(Interaction, Interaction.app_id == App.id)
        .join(Evaluation, Evaluation.interaction_id == Interaction.id)
        .where(Evaluation.ground_truth_is_problem.isnot(None))
    ).all()
    tally: dict[str, list[int]] = {}
    for name, is_problem in rows:
        entry = tally.setdefault(name, [0, 0])
        entry[0] += 1
        entry[1] += 1 if is_problem else 0
    return [(name, total, problems) for name, (total, problems) in sorted(tally.items())]


def findings_by_method(db) -> dict[str, dict[str, int]]:
    """Count findings as {dimension: {method: count}}.

    Async analyzer findings live on the evaluation; the Data Plane's synchronous catches
    live on the interaction and are always deterministic by construction, so they are
    folded in under their own dimension rather than being silently dropped.
    """
    tally: dict[str, dict[str, int]] = {}

    def add(dimension: str, method: str) -> None:
        tally.setdefault(dimension, {}).setdefault(method, 0)
        tally[dimension][method] += 1

    for (flags,) in db.execute(select(Evaluation.flags)).all():
        for flag in flags or []:
            add(flag.get("dimension", "unknown"), flag.get("method", "unknown"))

    for (sync_flags,) in db.execute(select(Interaction.sync_flags)).all():
        for _ in sync_flags or []:
            add("data_plane (sync)", "deterministic")

    return tally


def sample_texts(db, limit: int = 200) -> list[str]:
    """Prompt and response text for the latency benchmark to run against.

    Real corpus text rather than synthetic filler, so the pattern engine sees the same
    length distribution and the same near-miss candidates it sees in production.
    """
    rows = db.execute(select(Interaction.prompt, Interaction.raw_response).limit(limit)).all()
    texts: list[str] = []
    for prompt, response in rows:
        if prompt:
            texts.append(prompt)
        if response:
            texts.append(response)
    return texts


def detection_outcomes(db) -> dict[str, int]:
    """Detection-layer confusion counts: did the interaction produce *any* finding at all?

    This is a different question from the one section on routing asks. A finding can be
    recorded without changing how the response is handled, so detection recall and routing
    recall are genuinely separate measurements and are reported separately.
    """
    rows = db.execute(
        select(Evaluation.ground_truth_is_problem, Evaluation.flags, Interaction.sync_flags)
        .join(Interaction, Interaction.id == Evaluation.interaction_id)
        .where(Evaluation.ground_truth_is_problem.isnot(None))
    ).all()

    tp = fp = fn = tn = 0
    for is_problem, flags, sync_flags in rows:
        flagged = bool(flags) or bool(sync_flags)
        if flagged and is_problem:
            tp += 1
        elif flagged and not is_problem:
            fp += 1
        elif not flagged and is_problem:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def detected_but_not_routed(db, boundary: float = 90.0) -> list[tuple[str, int]]:
    """Problems that produced a finding but still scored above the first tier boundary.

    The gap between detection and routing, by scenario label. Reported because it is the
    clearest limitation the corpus exposes.
    """
    rows = db.execute(
        select(Evaluation.ground_truth_label)
        .where(
            Evaluation.ground_truth_is_problem.is_(True),
            Evaluation.trust_score >= boundary,
        )
    ).all()
    tally: dict[str, int] = {}
    for (label,) in rows:
        tally[label or "unlabelled"] = tally.get(label or "unlabelled", 0) + 1
    return sorted(tally.items(), key=lambda r: -r[1])


def clean_score_margin(db, boundary: float = 90.0) -> dict[str, float]:
    """How close the cleanest-scoring clean interaction came to the first tier boundary."""
    scores = [
        row[0]
        for row in db.execute(
            select(Evaluation.trust_score).where(Evaluation.ground_truth_is_problem.is_(False))
        ).all()
    ]
    if not scores:
        return {"min": 0.0, "boundary": boundary, "margin": 0.0, "n": 0}
    return {
        "min": min(scores),
        "boundary": boundary,
        "margin": round(min(scores) - boundary, 1),
        "n": len(scores),
    }


def false_positive_sources(db) -> list[tuple[str, int]]:
    """Which detectors fire on clean traffic, and how often.

    Aggregate precision says how noisy the system is; this says *where* the noise comes
    from, which is the only version of the number that tells you what to fix.
    """
    rows = db.execute(
        select(Evaluation.flags, Interaction.sync_flags)
        .join(Interaction, Interaction.id == Evaluation.interaction_id)
        .where(Evaluation.ground_truth_is_problem.is_(False))
    ).all()

    tally: dict[str, int] = {}
    for flags, sync_flags in rows:
        for flag in (flags or []):
            key = flag.get("type", "unknown")
            tally[key] = tally.get(key, 0) + 1
        for flag in (sync_flags or []):
            key = f"{flag.get('type', 'unknown')} (sync)"
            tally[key] = tally.get(key, 0) + 1
    return sorted(tally.items(), key=lambda r: -r[1])
