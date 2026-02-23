import unittest
import uuid
from types import SimpleNamespace

from app.services.permission_service import PermissionService


class TaskPermissionServiceTests(unittest.TestCase):
    def test_assignee_member_allowed_fields(self) -> None:
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        task = SimpleNamespace(
            assignee_id=member.id,
            created_by_id=uuid.uuid4(),
        )

        allowed = PermissionService.allowed_task_edit_fields(member, task)

        self.assertEqual(allowed, {"status", "checklist", "title"})
        self.assertTrue(PermissionService.can_edit_task(member, task))
        self.assertFalse(PermissionService.can_assign_task(member, task))
        self.assertTrue(PermissionService.can_change_task_status(member, task))
        self.assertTrue(PermissionService.can_add_task_update(member, task))

    def test_author_member_allowed_fields_and_assign(self) -> None:
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        task = SimpleNamespace(
            assignee_id=uuid.uuid4(),
            created_by_id=member.id,
        )

        allowed = PermissionService.allowed_task_edit_fields(member, task)

        self.assertEqual(
            allowed,
            {"status", "checklist", "title", "description", "priority", "deadline", "assignee_id"},
        )
        self.assertTrue(PermissionService.can_edit_task(member, task))
        self.assertTrue(PermissionService.can_assign_task(member, task))
        self.assertTrue(PermissionService.can_change_task_status(member, task))
        self.assertTrue(PermissionService.can_add_task_update(member, task))

    def test_moderator_has_full_task_permissions(self) -> None:
        member = SimpleNamespace(id=uuid.uuid4(), role="moderator")
        task = SimpleNamespace(
            assignee_id=uuid.uuid4(),
            created_by_id=uuid.uuid4(),
        )

        allowed = PermissionService.allowed_task_edit_fields(member, task)

        self.assertEqual(
            allowed,
            {"status", "checklist", "title", "description", "priority", "deadline", "assignee_id"},
        )
        self.assertTrue(PermissionService.can_edit_task(member, task))
        self.assertTrue(PermissionService.can_assign_task(member, task))
        self.assertTrue(PermissionService.can_change_task_status(member, task))
        self.assertTrue(PermissionService.can_add_task_update(member, task))

    def test_unrelated_member_has_no_edit_permissions(self) -> None:
        member = SimpleNamespace(id=uuid.uuid4(), role="member")
        task = SimpleNamespace(
            assignee_id=uuid.uuid4(),
            created_by_id=uuid.uuid4(),
        )

        self.assertEqual(PermissionService.allowed_task_edit_fields(member, task), set())
        self.assertFalse(PermissionService.can_edit_task(member, task))
        self.assertFalse(PermissionService.can_assign_task(member, task))
        self.assertFalse(PermissionService.can_change_task_status(member, task))
        self.assertFalse(PermissionService.can_add_task_update(member, task))
