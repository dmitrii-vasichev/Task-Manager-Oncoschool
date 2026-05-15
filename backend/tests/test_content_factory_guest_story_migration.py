from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "042_content_factory_guest_story.py"
)
EVENT_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "043_content_factory_guest_story_events.py"
)


def test_guest_story_migration_creates_table_and_consent_columns():
    source = MIGRATION.read_text()

    assert 'revision: str = "042_content_factory_guest_story"' in source
    assert 'down_revision: Union[str, None] = "041"' in source
    assert '"cf_guest_story"' in source
    assert '"display_name"' in source
    assert '"status"' in source
    assert '"owner_id"' in source
    assert '"consent_status"' in source
    assert '"consent_version"' in source
    assert '"consent_signed_at"' in source
    assert '"allowed_channels"' in source
    assert '"anonymity_level"' in source
    assert '"sensitive_topics"' in source
    assert '"legal_notes"' in source
    assert '"gift_status"' in source
    assert '"follow_up_due_at"' in source


def test_guest_story_migration_indexes_and_downgrade():
    source = MIGRATION.read_text()

    assert '"ix_cf_guest_story_status"' in source
    assert '"ix_cf_guest_story_owner"' in source
    assert '"ix_cf_guest_story_bundle"' in source
    assert '"ix_cf_guest_story_publication"' in source
    assert '"ix_cf_guest_story_stage_due"' in source
    assert 'op.drop_table("cf_guest_story")' in source


def test_guest_story_event_migration_creates_table_and_indexes():
    source = EVENT_MIGRATION.read_text()

    assert 'revision: str = "043_content_factory_guest_story_events"' in source
    assert 'down_revision: Union[str, None] = "042_content_factory_guest_story"' in source
    assert '"cf_guest_story_event"' in source
    assert '"guest_story_id"' in source
    assert '"actor_id"' in source
    assert '"event_type"' in source
    assert '"body"' in source
    assert '"old_value"' in source
    assert '"new_value"' in source
    assert '"payload"' in source
    assert '"ix_cf_guest_story_event_story_created"' in source
    assert '"ix_cf_guest_story_event_type"' in source
    assert 'op.drop_table("cf_guest_story_event")' in source
