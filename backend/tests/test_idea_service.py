import unittest

from pydantic import ValidationError
from sqlalchemy import ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import configure_mappers

from app.db import models
from app.db.schemas import IdeaCreate, IdeaStatusChange


class IdeaModelSmokeTests(unittest.TestCase):
    def test_idea_models_are_registered(self) -> None:
        table_names = set(models.Base.metadata.tables)

        self.assertIn("ideas", table_names)
        self.assertIn("idea_departments", table_names)
        self.assertIn("idea_tasks", table_names)
        self.assertIn("idea_comments", table_names)
        self.assertIn("idea_events", table_names)

    def test_idea_relationship_mappers_configure(self) -> None:
        configure_mappers()
        self.assertTrue(models.IdeaDepartment.task_links.property.viewonly)
        self.assertTrue(models.IdeaTask.idea_department.property.viewonly)

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


class IdeaSchemaTests(unittest.TestCase):
    def test_create_idea_requires_non_empty_title_and_description(self) -> None:
        with self.assertRaises(ValidationError):
            IdeaCreate(title="", description="Useful details", review_owner_id="00000000-0000-0000-0000-000000000001")

        with self.assertRaises(ValidationError):
            IdeaCreate(title="Improve reports", description="", review_owner_id="00000000-0000-0000-0000-000000000001")

    def test_rejected_and_deferred_status_changes_require_reason(self) -> None:
        with self.assertRaises(ValidationError):
            IdeaStatusChange(status="rejected")

        with self.assertRaises(ValidationError):
            IdeaStatusChange(status="deferred")

        with self.assertRaises(ValidationError):
            IdeaStatusChange(status="rejected", comment="")

        with self.assertRaises(ValidationError):
            IdeaStatusChange(status="deferred", comment="   ")

    def test_accepted_status_change_allows_empty_comment(self) -> None:
        data = IdeaStatusChange(status="accepted")
        self.assertEqual(data.status, "accepted")
        self.assertIsNone(data.comment)
