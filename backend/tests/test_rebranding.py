"""Tests for Phase R4 rebranding: Task Manager → Portal."""


def test_fastapi_app_title_contains_portal():
    """FastAPI app title should say 'Portal', not 'Task Manager'."""
    from app.main import app

    assert "Portal" in app.title
    assert "Task Manager" not in app.title


def test_bot_auth_message_contains_portal():
    """Web login confirmation message should reference 'Портал', not 'Task Manager'."""
    import inspect
    from app.bot.handlers.common import send_web_login_confirmation

    source = inspect.getsource(send_web_login_confirmation)
    assert "Портал Онкошколы" in source
    assert "Task Manager" not in source


def test_pyproject_description_contains_portal():
    """pyproject.toml description should say 'Portal', not 'Task Manager'."""
    from pathlib import Path

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "Portal" in content
    # description line should not reference Task Manager
    for line in content.splitlines():
        if line.startswith("description"):
            assert "Task Manager" not in line
            break
