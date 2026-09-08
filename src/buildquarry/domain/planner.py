"""Deterministic first-pass planning engine."""

import re

from buildquarry.domain.models import Milestone, Plan, ProjectInput

TIME_LIMITS = {
    "weekend": 3,
    "one_week": 5,
    "two_weeks": 8,
    "one_month": 12,
}

FEATURE_WORDS = (
    "authentication",
    "accounts",
    "chat",
    "payments",
    "analytics",
    "notifications",
    "search",
    "dashboard",
    "mobile app",
    "integrations",
    "recommendations",
    "export",
)


def _candidate_features(idea: str) -> list[str]:
    lowered = idea.lower()
    found = [feature for feature in FEATURE_WORDS if feature in lowered]
    if found:
        return found
    return ["core input flow", "primary result view", "local persistence"]


def _title(idea: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", idea)
    return " ".join(words[:8]).strip().capitalize() or "Focused project"


def create_plan(project: ProjectInput) -> Plan:
    features = _candidate_features(project.idea)
    limit = TIME_LIMITS[project.time_budget]
    in_scope = features[: min(3, len(features))]
    out_of_scope = features[3:] or ["Team collaboration", "Billing", "Advanced integrations"]
    tasks = [
        "Define the smallest user workflow",
        f"Build {in_scope[0]}",
        "Add validation and a useful success state",
        "Test the complete workflow",
        "Document setup and next steps",
    ]
    tasks = tasks[:limit]
    split = max(1, len(tasks) // 3)
    milestones = [
        Milestone(title="Define the workflow", tasks=tasks[:split]),
        Milestone(title="Build the core path", tasks=tasks[split : split * 2]),
        Milestone(title="Verify and ship", tasks=tasks[split * 2 :]),
    ]
    milestones = [milestone for milestone in milestones if milestone.tasks]
    return Plan(
        title=_title(project.idea),
        mvp=f"Build one reliable workflow for {project.target_user}: {project.idea.strip()}",
        primary_user=project.target_user,
        in_scope=in_scope,
        out_of_scope=out_of_scope,
        milestones=milestones,
        acceptance_criteria=[
            "A user can complete the primary workflow end to end.",
            "Invalid or incomplete input produces a clear error.",
            "Plan stays within the selected time budget.",
        ],
    )
