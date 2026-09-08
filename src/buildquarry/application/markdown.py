"""Markdown serialization for editable plans."""

from buildquarry.domain.models import Plan


def plan_to_markdown(plan: Plan) -> str:
    lines = [
        f"# {plan.title}",
        "",
        f"**Primary user:** {plan.primary_user}",
        "",
        "## Focused MVP",
        plan.mvp,
        "",
        "## In scope",
        *[f"- {item}" for item in plan.in_scope],
        "",
        "## Out of scope",
        *[f"- {item}" for item in plan.out_of_scope],
        "",
        "## Milestones",
    ]
    for index, milestone in enumerate(plan.milestones, start=1):
        lines.extend([f"### {index}. {milestone.title}", *[f"- {task}" for task in milestone.tasks], ""])
    lines.extend(["## Acceptance criteria", *[f"- {item}" for item in plan.acceptance_criteria], ""])
    sections = (
        ("Architecture", plan.architecture),
        ("Data model", plan.data_model),
        ("API design", plan.api_design),
        ("Technical risks", plan.technical_risks),
        ("Implementation notes", plan.implementation_notes),
    )
    for title, items in sections:
        if items:
            lines.extend([f"## {title}", *[f"- {item}" for item in items], ""])
    return "\n".join(lines)
