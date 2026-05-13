import unittest

from app.db import models


class IdeaModelSmokeTests(unittest.TestCase):
    def test_idea_models_are_registered(self) -> None:
        table_names = {table.name for table in models.Base.metadata.sorted_tables}

        self.assertIn("ideas", table_names)
        self.assertIn("idea_departments", table_names)
        self.assertIn("idea_tasks", table_names)
        self.assertIn("idea_comments", table_names)
        self.assertIn("idea_events", table_names)
