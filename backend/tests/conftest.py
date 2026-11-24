import os
import sys
import tempfile
from pathlib import Path

import pytest

# Use a throwaway SQLite database so tests never touch real data.
_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp_dir) / 'test.db'}"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def fake_ai(monkeypatch):
    """Replace the Azure OpenAI client. Never calls Azure.

    Usage: calls = fake_ai(scope_reply='{"in_scope": true}', draft_reply={...})
    The scope check gets scope_reply; every other prompt gets draft_reply.
    calls is a list of ("scope" | "draft", prompt) in call order.
    """
    import json
    from types import SimpleNamespace

    from app.services import llm_service

    def setup(scope_reply='{"in_scope": true}', draft_reply=None):
        calls = []

        def fake_create(**kwargs):
            prompt = kwargs["messages"][0]["content"]
            kind = "scope" if prompt.startswith("You screen records") else "draft"
            calls.append((kind, prompt))
            reply = scope_reply if kind == "scope" else draft_reply
            content = reply if isinstance(reply, str) else json.dumps(reply or {})
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])

        monkeypatch.setattr(llm_service, "client", SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create))
        ))
        return calls

    return setup
