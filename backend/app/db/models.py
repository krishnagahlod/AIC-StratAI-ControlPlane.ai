import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


class App(Base):
    __tablename__ = "apps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(128))
    app_type: Mapped[str] = mapped_column(String(32))  # customer_facing | internal | decision_support
    latency_budget_ms: Mapped[int] = mapped_column(Integer, default=3000)
    risk_tolerance: Mapped[str] = mapped_column(String(16), default="medium")
    weight_performance: Mapped[float] = mapped_column(Float, default=0.4)
    weight_cost: Mapped[float] = mapped_column(Float, default=0.3)
    weight_responsibility: Mapped[float] = mapped_column(Float, default=0.3)
    daily_budget_usd: Mapped[float] = mapped_column(Float, default=25.0)

    interactions: Mapped[list["Interaction"]] = relationship(back_populates="app")


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    task_type: Mapped[str] = mapped_column(String(64), default="general")
    prompt: Mapped[str] = mapped_column(Text)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    rag_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[str] = mapped_column(Text)
    delivered_response: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(64))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    sync_action: Mapped[str] = mapped_column(String(16), default="allowed")  # allowed|redacted|blocked
    sync_flags: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(16), default="live")  # live|seed

    app: Mapped["App"] = relationship(back_populates="interactions")
    evaluation: Mapped["Evaluation"] = relationship(back_populates="interaction", uselist=False)
    business_impact: Mapped["BusinessImpact"] = relationship(back_populates="interaction", uselist=False)
    escalation: Mapped["Escalation"] = relationship(back_populates="interaction", uselist=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    performance_score: Mapped[float] = mapped_column(Float)
    cost_score: Mapped[float] = mapped_column(Float)
    responsibility_score: Mapped[float] = mapped_column(Float)
    trust_score: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(16))
    response_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    flags: Mapped[list] = mapped_column(JSON, default=list)
    ground_truth_is_problem: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    ground_truth_label: Mapped[str | None] = mapped_column(String(64), nullable=True)

    interaction: Mapped["Interaction"] = relationship(back_populates="evaluation")


class BusinessImpact(Base):
    __tablename__ = "business_impact"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), unique=True)
    risk_category: Mapped[str] = mapped_column(String(32))
    estimated_impact_usd: Mapped[float] = mapped_column(Float, default=0.0)
    affected_users: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    narrative: Mapped[str] = mapped_column(Text)

    interaction: Mapped["Interaction"] = relationship(back_populates="business_impact")


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interaction_id: Mapped[int] = mapped_column(ForeignKey("interactions.id"), unique=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    decision: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="resolved")
    sla_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sla_deadline: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    reviewer_decision: Mapped[str | None] = mapped_column(String(24), nullable=True)
    reviewer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    interaction: Mapped["Interaction"] = relationship(back_populates="escalation")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int | None] = mapped_column(ForeignKey("apps.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    issue: Mapped[str] = mapped_column(Text)
    root_cause: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    expected_impact: Mapped[str] = mapped_column(Text)
    estimated_value_usd: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    method: Mapped[str] = mapped_column(String(16), default="rule_based")  # rule_based|llm_generated


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=utcnow)
    severity: Mapped[str] = mapped_column(String(16))
    dedup_key: Mapped[str] = mapped_column(String(128))
    count: Mapped[int] = mapped_column(Integer, default=1)
    message: Mapped[str] = mapped_column(Text)
    app_id: Mapped[int | None] = mapped_column(ForeignKey("apps.id"), nullable=True)
    interaction_id: Mapped[int | None] = mapped_column(ForeignKey("interactions.id"), nullable=True)
