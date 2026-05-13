import unittest

from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from app.db import models


class IdeaModelSmokeTests(unittest.TestCase):
    def test_idea_models_are_registered(self) -> None:
        table_names = {table.name for table in models.Base.metadata.sorted_tables}

        self.assertIn("ideas", table_names)
        self.assertIn("idea_departments", table_names)
        self.assertIn("idea_tasks", table_names)
        self.assertIn("idea_comments", table_names)
        self.assertIn("idea_events", table_names)

    def test_idea_relationship_mappers_configure(self) -> None:
        configure_mappers()

    def test_idea_task_department_link_is_scoped_to_same_idea(self) -> None:
        idea_departments = models.IdeaDepartment.__table__
        idea_tasks = models.IdeaTask.__table__

        unique_constraints = {
            constraint.name
            for constraint in idea_departments.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        composite_fk_targets = {
            tuple(element.target_fullname for element in constraint.elements)
            for constraint in idea_tasks.constraints
            if isinstance(constraint, ForeignKeyConstraint)
        }

        self.assertIn("uq_idea_departments_idea_id_id", unique_constraints)
        self.assertIn(
            ("idea_departments.idea_id", "idea_departments.id"),
            composite_fk_targets,
        )
