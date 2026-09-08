import unittest

from buildquarry.application.markdown import plan_to_markdown
from buildquarry.domain.models import ProjectInput
from buildquarry.domain.planner import create_plan
from buildquarry.domain.scope_rules import enforce_scope


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = ProjectInput(
            idea="Build a developer planning tool with chat and payments",
            target_user="independent developers",
            time_budget="weekend",
            skill_level="Intermediate",
        )

    def test_manual_plan_respects_weekend_scope(self) -> None:
        plan = enforce_scope(create_plan(self.project), self.project)
        self.assertLessEqual(len(plan.in_scope), 3)
        self.assertTrue(plan.out_of_scope)
        self.assertTrue(plan.milestones)

    def test_markdown_contains_editable_sections(self) -> None:
        markdown = plan_to_markdown(create_plan(self.project))
        self.assertIn("## In scope", markdown)
        self.assertIn("## Out of scope", markdown)
        self.assertIn("## Milestones", markdown)
        self.assertIn("## Acceptance criteria", markdown)


if __name__ == "__main__":
    unittest.main()
