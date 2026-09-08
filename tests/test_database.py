import tempfile
import unittest
from pathlib import Path

from buildquarry.infrastructure.database import PlanDatabase


class DatabaseTests(unittest.TestCase):
    def test_save_update_list_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = PlanDatabase(Path(directory) / "plans.sqlite3")
            plan_id = database.save("First plan", "# First plan")
            self.assertEqual(database.get(plan_id).markdown, "# First plan")
            database.save("Updated plan", "# Updated plan", plan_id)
            self.assertEqual(database.list_plans()[0].title, "Updated plan")
            database.delete(plan_id)
            self.assertEqual(database.list_plans(), [])
            database.close()


if __name__ == "__main__":
    unittest.main()
