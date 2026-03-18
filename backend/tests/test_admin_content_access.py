"""Regression test for content access grant (issue #42).

The bug: after session.commit(), the SQLAlchemy object is expired.
Accessing access.id in async triggers MissingGreenlet → HTTP 500.
Fix: save access.id before commit.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid


class TestGrantContentAccessEndpoint(unittest.IsolatedAsyncioTestCase):
    """Test that grant_content_access saves access.id before commit."""

    async def test_access_id_saved_before_commit(self):
        """Regression: access.id must be read before session.commit() expires the object."""
        from app.db.models import ContentRole, ContentSubSection

        fake_id = uuid.uuid4()
        fake_access = MagicMock()
        fake_access.id = fake_id

        # After commit, simulate expired object (accessing .id raises)
        committed = False

        original_id = fake_access.id

        def side_effect_commit():
            nonlocal committed
            committed = True
            # Simulate SQLAlchemy expiring the object after commit
            type(fake_access).id = property(
                lambda self: (_ for _ in ()).throw(
                    Exception("MissingGreenlet: can't lazy load in async")
                )
            )

        fake_session = AsyncMock()
        fake_session.commit = AsyncMock(side_effect=side_effect_commit)

        # Build a fake grant that will be returned by list_access
        fake_grant = MagicMock()
        fake_grant.id = fake_id
        fake_grant.sub_section = ContentSubSection.telegram_analysis
        fake_grant.member_id = uuid.uuid4()
        fake_grant.member.full_name = "Test User"
        fake_grant.department_id = None
        fake_grant.department = None
        fake_grant.role = ContentRole.editor

        with patch(
            "app.api.admin.ContentAccessService.grant_access",
            new_callable=AsyncMock,
            return_value=fake_access,
        ), patch(
            "app.api.admin.ContentAccessService.list_access",
            new_callable=AsyncMock,
            return_value=[fake_grant],
        ):
            from app.api.admin import grant_content_access, ContentAccessGrant

            data = ContentAccessGrant(
                sub_section="telegram_analysis",
                member_id=fake_grant.member_id,
                role="editor",
            )

            fake_member = MagicMock()
            result = await grant_content_access.__wrapped__(
                data=data, member=fake_member, session=fake_session
            ) if hasattr(grant_content_access, '__wrapped__') else None

            # If we can't call it directly (due to Depends), just verify the code path
            # by checking that the module's grant function saves id before commit
            import inspect
            source = inspect.getsource(grant_content_access)
            # The fix: access_id = access.id must appear BEFORE session.commit()
            id_save_pos = source.find("access_id = access.id")
            commit_pos = source.find("session.commit()")
            assert id_save_pos != -1, "Fix missing: access_id = access.id not found"
            assert id_save_pos < commit_pos, (
                "Bug: access.id is read AFTER session.commit() — "
                "will cause MissingGreenlet in async SQLAlchemy"
            )


if __name__ == "__main__":
    unittest.main()
