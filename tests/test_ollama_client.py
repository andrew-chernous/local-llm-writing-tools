import io
import json
import subprocess
import urllib.error

import pytest

import ollama_client
from ollama_client import OllamaError, chat, get_clipboard


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(reply: str, sent: list):
    def _urlopen(req, timeout):
        sent.append(json.loads(req.data))
        return FakeResponse(json.dumps({"message": {"content": reply}}).encode("utf-8"))

    return _urlopen


def raise_on_urlopen(error: Exception):
    def _urlopen(req, timeout):
        raise error

    return _urlopen


def test_chat_returns_stripped_reply_and_disables_thinking(monkeypatch):
    sent = []
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", fake_urlopen("  Hi there  \n", sent))

    assert chat("m", "sys", "hi", {"temperature": 0.3}) == "Hi there"

    payload = sent[0]
    assert payload["model"] == "m"
    assert payload["think"] is False
    assert payload["options"]["temperature"] == 0.3
    assert payload["options"]["num_predict"] == ollama_client.MAX_OUTPUT_TOKENS


def test_chat_empty_reply_raises_so_clipboard_is_not_overwritten(monkeypatch):
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", fake_urlopen("   ", []))

    with pytest.raises(OllamaError, match="empty response"):
        chat("m", "sys", "hi", {})


def test_chat_missing_model_tells_user_to_pull_it(monkeypatch):
    error = urllib.error.HTTPError(ollama_client.OLLAMA_URL, 404, "Not Found", {}, io.BytesIO(b""))
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", raise_on_urlopen(error))

    with pytest.raises(OllamaError, match="ollama pull gemma-x"):
        chat("gemma-x", "sys", "hi", {})


def test_chat_ollama_down_tells_user_to_start_it(monkeypatch):
    error = urllib.error.URLError(ConnectionRefusedError(61, "Connection refused"))
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", raise_on_urlopen(error))

    with pytest.raises(OllamaError, match="ollama serve"):
        chat("m", "sys", "hi", {})


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Привіт — 👋".encode(), "Привіт — 👋"),
        ("Привет".encode("cp1251"), "Привет"),
    ],
)
def test_get_clipboard_decodes_utf8_and_windows_cyrillic(monkeypatch, raw, expected):
    monkeypatch.setattr(
        ollama_client.subprocess,
        "run",
        lambda *a, **kw: subprocess.CompletedProcess(a, 0, stdout=raw),
    )

    assert get_clipboard() == expected
