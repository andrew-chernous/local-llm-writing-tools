#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Proofread
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon ✍️
# @raycast.packageName Local LLM Writing Tools
# Note: Raycast preselects the FIRST item of a dropdown, so the order below
# defines the defaults: B1-B2 / Fix only / gemma4:e4b-it-qat.
# @raycast.argument1 { "type": "dropdown", "placeholder": "Level", "data": [{"title": "B1-B2", "value": "b1-b2"}, {"title": "B1", "value": "b1"}, {"title": "B2", "value": "b2"}] }
# @raycast.argument2 { "type": "dropdown", "placeholder": "Depth", "data": [{"title": "Fix only", "value": "fix"}, {"title": "Fix + explain", "value": "explain"}] }
# @raycast.argument3 { "type": "dropdown", "placeholder": "Model", "data": [{"title": "gemma4:e4b-it-qat", "value": "gemma4:e4b-it-qat"}, {"title": "gemma4:e4b", "value": "gemma4:e4b"}] }

# Documentation:
# @raycast.description Fix spelling and grammar while keeping the text at B1/B2 level
# @raycast.author Andrew Chernous

import sys

from ollama_client import OllamaError, chat, get_clipboard, set_clipboard

# Separator between the corrected text and the Notes.
# Unlikely to appear in real text, and easy to split on.
NOTES_MARKER = "===NOTES==="

LEVEL_HINTS = {
    "b1": (
        "CEFR B1. Use common everyday vocabulary and simple sentence structures. "
        "Prefer short sentences. Avoid idioms, phrasal-verb pileups and rare words."
    ),
    "b2": (
        "CEFR B2. Use clear, natural vocabulary with some range. Compound sentences are fine. "
        "Avoid academic, literary or overly sophisticated wording."
    ),
    "b1-b2": (
        "CEFR B1-B2. Use clear everyday vocabulary that a confident intermediate speaker would "
        "actually use. Simple to moderately complex sentences. No academic or literary flourishes."
    ),
}

DEPTH_HINTS = {
    "fix": (
        f"Return ONLY the corrected text. Do NOT output the {NOTES_MARKER} marker "
        "and do NOT add any explanation."
    ),
    "explain": (
        "After the corrected text, output the marker "
        f"{NOTES_MARKER} on its own line, then a short bullet list of the most "
        "important corrections. Each bullet: what was wrong -> what it became -> why, "
        "in one line. Maximum 7 bullets, skip trivial typos."
    ),
}

# Lower than Rephrase on purpose: proofreading should be predictable and
# boring, not creative.
SAMPLING = {"temperature": 0.3, "top_p": 0.9, "top_k": 40}


def build_system_prompt(level: str, depth: str) -> str:
    return (
        "You are an English proofreader for a non-native speaker. "
        "Your job is to fix mistakes, NOT to make the text sound more advanced.\n"
        "Rules:\n"
        "- Fix spelling, grammar, articles, prepositions, word order and punctuation.\n"
        f"- Keep the text at this level: {LEVEL_HINTS[level]}\n"
        "- Keep the author's own voice and word choice whenever it is already correct. "
        "If a sentence is grammatically fine, leave it alone even if you would phrase it better.\n"
        "- Do not add new information, do not remove information, keep approximately the same length.\n"
        "- Preserve all markdown formatting exactly as in the input: "
        "inline code with backticks (`like this`), fenced code blocks (```), "
        "bold (**word**), italics (*word*), links, lists, and line breaks. "
        "Never correct anything inside code blocks or inline code.\n"
        "- Do NOT wrap your entire response in a code block or quotes.\n"
        "- No preamble like 'Here is the corrected version'.\n"
        f"- {DEPTH_HINTS[depth]}"
    )


def split_result(raw: str) -> tuple[str, str]:
    """Split the model output into (corrected_text, notes); notes may be empty.

    Always tries to split, because small models sometimes emit the marker even
    in "fix" mode, and the Notes must never reach the clipboard.
    """
    if NOTES_MARKER in raw:
        corrected, _, notes = raw.partition(NOTES_MARKER)
        return corrected.strip(), notes.strip()
    return raw, ""


def main() -> None:
    level, depth, model = sys.argv[1], sys.argv[2], sys.argv[3]

    source = get_clipboard()
    if not source.strip():
        print("Clipboard is empty. Copy some text first (Cmd+C) and try again.")
        sys.exit(1)

    try:
        raw = chat(model, build_system_prompt(level, depth), source, SAMPLING)
    except OllamaError as e:
        print(f"⚠️  {e}")
        sys.exit(1)

    corrected, notes = split_result(raw)

    set_clipboard(corrected)

    print(f"✅ Copied to clipboard ({level} / {depth} / {model})\n")
    print("─" * 40)
    print(corrected)

    if notes:
        print("\n" + "─" * 40)
        print("📝 What changed and why:\n")
        print(notes)


if __name__ == "__main__":
    main()
