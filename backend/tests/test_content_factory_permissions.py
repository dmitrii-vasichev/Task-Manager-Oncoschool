import uuid
from types import SimpleNamespace

from app.services.permission_service import PermissionService


def member(
    role: str = "member",
    *,
    is_active: bool = True,
    has_cf_access: bool = False,
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        role=role,
        is_active=is_active,
        has_content_factory_access=has_cf_access,
    )


# ── Access ──

def test_admin_has_cf_access_implicitly():
    assert PermissionService.can_access_content_factory(member("admin")) is True


def test_member_with_flag_has_cf_access():
    assert (
        PermissionService.can_access_content_factory(
            member("member", has_cf_access=True)
        )
        is True
    )


def test_moderator_without_flag_has_no_cf_access():
    # Moderator role alone is NOT enough anymore.
    assert PermissionService.can_access_content_factory(member("moderator")) is False


def test_regular_member_without_flag_cannot_access():
    assert PermissionService.can_access_content_factory(member("member")) is False


def test_inactive_admin_cannot_access_cf():
    assert (
        PermissionService.can_access_content_factory(member("admin", is_active=False))
        is False
    )


def test_inactive_flagged_member_cannot_access_cf():
    assert (
        PermissionService.can_access_content_factory(
            member("member", has_cf_access=True, is_active=False)
        )
        is False
    )


# ── Editing / approving / publishing — same gate ──

def test_flagged_member_can_edit_bundle():
    assert (
        PermissionService.can_edit_cf_bundle(member("member", has_cf_access=True))
        is True
    )


def test_flagged_member_can_approve_publication():
    assert (
        PermissionService.can_approve_cf_publication(
            member("member", has_cf_access=True)
        )
        is True
    )


def test_flagged_member_can_create_retro():
    assert (
        PermissionService.can_create_cf_retro(member("member", has_cf_access=True))
        is True
    )


# ── Reference tables — admin only ──

def test_admin_can_edit_reference_tables():
    assert PermissionService.can_edit_cf_reference_tables(member("admin")) is True


def test_flagged_member_cannot_edit_reference_tables():
    assert (
        PermissionService.can_edit_cf_reference_tables(
            member("member", has_cf_access=True)
        )
        is False
    )


def test_moderator_cannot_edit_reference_tables():
    assert PermissionService.can_edit_cf_reference_tables(member("moderator")) is False
