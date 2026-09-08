import json
import unittest
from unittest.mock import patch

from buildquarry.domain.models import ProjectInput
from buildquarry.infrastructure.gemini import GeminiError, create_gemini_plan


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class GeminiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project = ProjectInput(
            idea="Build a focused developer planning tool",
            target_user="developers",
            time_budget="one_week",
            skill_level="Intermediate",
        )

    @patch("buildquarry.infrastructure.gemini.urlopen")
    def test_structured_response_is_validated(self, urlopen) -> None:
        plan = {
            "title": "Planner",
            "mvp": "One planning flow",
            "primary_user": "developers",
            "in_scope": ["brief form"],
            "out_of_scope": ["teams"],
            "milestones": [{"title": "Core", "tasks": ["Build form"]}],
            "acceptance_criteria": ["Form submits"],
            "architecture": ["PySide6 UI"],
        }
        urlopen.return_value = FakeResponse(
            {"candidates": [{"content": {"parts": [{"text": json.dumps(plan)}]}}]}
        )
        result = create_gemini_plan(self.project, "valid-key", "gemini-3.6-flash")
        self.assertEqual(result.architecture, ["PySide6 UI"])

    @patch("buildquarry.infrastructure.gemini.urlopen")
    def test_malformed_response_raises_gemini_error(self, urlopen) -> None:
        urlopen.return_value = FakeResponse({"candidates": [{"content": {"parts": [{"text": "{}"}]}}]})
        with self.assertRaises(GeminiError):
            create_gemini_plan(self.project, "valid-key", "gemini-3.6-flash")


if __name__ == "__main__":
    unittest.main()
