"""Hard limits applied to manual and AI-generated plans."""

from buildquarry.domain.models import Plan, ProjectInput

MAX_FEATURES = {"weekend": 3, "one_week": 5, "two_weeks": 8, "one_month": 12}


def enforce_scope(plan: Plan, project: ProjectInput) -> Plan:
    feature_limit = min(3, MAX_FEATURES[project.time_budget])
    in_scope = plan.in_scope[:feature_limit]
    deferred = plan.in_scope[feature_limit:]
    milestones = plan.milestones[:MAX_FEATURES[project.time_budget]]
    return plan.model_copy(
        update={
            "in_scope": in_scope or ["Primary user workflow"],
            "out_of_scope": [*deferred, *plan.out_of_scope] or ["Advanced features"],
            "milestones": milestones or plan.milestones[:1],
        }
    )
