"""Data model and validation for an agentic AI use case."""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any

AUTONOMY_LEVELS = ("suggest", "draft", "act_with_approval", "act_autonomous")
REVERSIBILITY = ("reversible", "partially_reversible", "irreversible")
DATA_SENSITIVITY = ("public", "internal", "confidential", "regulated")
REGULATORY_SCOPE = ("none", "transparency", "high_risk")


class ValidationError(ValueError):
    """Raised when a use case file is missing fields or has invalid values."""


@dataclass(frozen=True)
class UseCase:
    # Identity
    name: str
    owner_function: str
    description: str = ""

    # Value
    tasks_per_month: int = 0
    minutes_saved_per_task: float = 0.0
    loaded_cost_per_hour_usd: float = 0.0
    other_annual_value_usd: float = 0.0  # revenue uplift, leakage avoided, etc.
    kpi_defined: bool = False  # a measurable success metric agreed up front
    exec_sponsor: bool = False

    # Readiness (0 = none, 5 = excellent)
    data_access: int = 0
    tool_apis: int = 0
    process_documented: int = 0
    eval_set_exists: bool = False
    observability_in_place: bool = False

    # Risk
    autonomy: str = "suggest"
    reversibility: str = "reversible"
    data_sensitivity: str = "internal"
    customer_facing: bool = False
    regulatory_scope: str = "none"

    # Cost
    est_annual_run_cost_usd: float = 0.0
    est_build_cost_usd: float = 0.0

    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "UseCase":
        known = {f.name for f in fields(cls)}
        unknown = set(raw) - known
        if unknown:
            raise ValidationError(f"Unknown field(s): {', '.join(sorted(unknown))}")
        for required in ("name", "owner_function"):
            if not raw.get(required):
                raise ValidationError(f"Missing required field: {required}")
        uc = cls(**raw)
        uc._validate()
        return uc

    def _validate(self) -> None:
        enums = {
            "autonomy": AUTONOMY_LEVELS,
            "reversibility": REVERSIBILITY,
            "data_sensitivity": DATA_SENSITIVITY,
            "regulatory_scope": REGULATORY_SCOPE,
        }
        for name, allowed in enums.items():
            value = getattr(self, name)
            if value not in allowed:
                raise ValidationError(f"{name}={value!r} not in {allowed}")
        for name in ("data_access", "tool_apis", "process_documented"):
            value = getattr(self, name)
            if not isinstance(value, int) or not 0 <= value <= 5:
                raise ValidationError(f"{name} must be an integer 0-5, got {value!r}")
        for name in (
            "tasks_per_month",
            "minutes_saved_per_task",
            "loaded_cost_per_hour_usd",
            "other_annual_value_usd",
            "est_annual_run_cost_usd",
            "est_build_cost_usd",
        ):
            if getattr(self, name) < 0:
                raise ValidationError(f"{name} cannot be negative")
