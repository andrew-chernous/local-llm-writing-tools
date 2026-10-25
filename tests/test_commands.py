import sys

import pytest

import proofread
import rephrase
import translate
from ollama_client import TONE_HINTS


def test_proofread_split_keeps_notes_off_the_clipboard_text():
    raw = f"Fixed text.\n{proofread.NOTES_MARKER}\n- teh -> the -> typo"

    assert proofread.split_result(raw) == ("Fixed text.", "- teh -> the -> typo")


def test_proofread_split_without_marker_returns_text_unchanged():
    assert proofread.split_result("Fixed text.") == ("Fixed text.", "")


def test_rephrase_and_translate_share_one_tone_definition():
    for tone, hint in TONE_HINTS.items():
        assert hint in rephrase.build_system_prompt("leadership", tone)
        assert hint in translate.build_system_prompt("auto", "en", tone)


def test_translate_auto_detect_prompt_does_not_name_a_source_language():
    prompt = translate.build_system_prompt("auto", "uk", "neutral")

    assert "Detect the source language automatically" in prompt
    assert "into Ukrainian" in prompt


def test_translate_same_language_exits_before_calling_the_model(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["translate.py", "en", "en", "neutral"])
    monkeypatch.setattr(translate, "get_clipboard", lambda: pytest.fail("clipboard read"))
    monkeypatch.setattr(translate, "chat", lambda *a: pytest.fail("model called"))

    with pytest.raises(SystemExit) as exit_info:
        translate.main()

    assert exit_info.value.code == 1
    assert "Nothing to translate" in capsys.readouterr().out


def test_proofread_explain_mode_copies_only_the_corrected_text(monkeypatch, capsys):
    copied = []
    raw = f"I went home.\n{proofread.NOTES_MARKER}\n- goed -> went -> irregular verb"
    monkeypatch.setattr(sys, "argv", ["proofread.py", "b1-b2", "explain", "m"])
    monkeypatch.setattr(proofread, "get_clipboard", lambda: "I goed home.")
    monkeypatch.setattr(proofread, "chat", lambda *a: raw)
    monkeypatch.setattr(proofread, "set_clipboard", copied.append)

    proofread.main()

    assert copied == ["I went home."]
    assert "irregular verb" in capsys.readouterr().out
