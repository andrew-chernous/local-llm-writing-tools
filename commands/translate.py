#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Translate
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 🌐
# @raycast.packageName Local LLM Writing Tools
# Raycast allows at most 3 arguments, so there is no Model dropdown here;
# the model comes from ollama_client.DEFAULT_MODEL.
# @raycast.argument1 { "type": "dropdown", "placeholder": "From", "data": [{"title": "Auto-detect", "value": "auto"}, {"title": "English", "value": "en"}, {"title": "Ukrainian", "value": "uk"}, {"title": "Russian", "value": "ru"}] }
# @raycast.argument2 { "type": "dropdown", "placeholder": "To", "data": [{"title": "English", "value": "en"}, {"title": "Ukrainian", "value": "uk"}, {"title": "Russian", "value": "ru"}] }
# @raycast.argument3 { "type": "dropdown", "placeholder": "Tone", "data": [{"title": "Friendly", "value": "friendly"}, {"title": "Neutral", "value": "neutral"}, {"title": "Formal", "value": "formal"}] }

# Documentation:
# @raycast.description Translate clipboard text between EN/UK/RU using a local LLM
# @raycast.author Andrew Chernous

import sys

from ollama_client import (
    DEFAULT_MODEL,
    TONE_HINTS,
    OllamaError,
    chat,
    get_clipboard,
    set_clipboard,
)

LANG_NAMES = {
    "en": "English",
    "uk": "Ukrainian",
    "ru": "Russian",
    "auto": "auto-detected",
}

# Translation needs idiomatic phrasing rather than literal word-for-word
# output, so this uses the same varied sampling as Rephrase.
SAMPLING = {"temperature": 1.0, "top_p": 0.95, "top_k": 64}


def build_system_prompt(src: str, dst: str, tone: str) -> str:
    src_clause = (
        "Detect the source language automatically (it will be English, Ukrainian, or Russian)."
        if src == "auto"
        else f"The source language is {LANG_NAMES[src]}."
    )
    return (
        "You are a professional translator working between English, Ukrainian, and Russian.\n"
        f"{src_clause}\n"
        f"Translate the user's text into {LANG_NAMES[dst]}.\n"
        "\n"
        "Style and register:\n"
        f"- {TONE_HINTS[tone]}\n"
        "- Translate idioms idiomatically, not word-for-word.\n"
        "- Preserve names, brands, code identifiers, URLs, and numbers as-is.\n"
        "\n"
        "Formatting:\n"
        "- Preserve all markdown exactly: inline code with backticks, fenced code blocks, "
        "bold, italics, links, lists, line breaks.\n"
        "- Do NOT translate text inside backticks or fenced code blocks; leave it as-is.\n"
        "- Do NOT wrap your entire response in a code block or quotes.\n"
        "\n"
        "Output:\n"
        "- Return ONLY the translated text. No preamble, no language labels, "
        "no explanations, no alternatives."
    )


def main() -> None:
    src, dst, tone = sys.argv[1], sys.argv[2], sys.argv[3]

    # Same source and target is almost always a misclick in the dropdown.
    if src != "auto" and src == dst:
        print(f"⚠️  Source and target are both {LANG_NAMES[src]}. Nothing to translate.")
        sys.exit(1)

    source = get_clipboard()
    if not source.strip():
        print("Clipboard is empty. Copy some text first (Cmd+C) and try again.")
        sys.exit(1)

    try:
        result = chat(DEFAULT_MODEL, build_system_prompt(src, dst, tone), source, SAMPLING)
    except OllamaError as e:
        print(f"⚠️  {e}")
        sys.exit(1)

    set_clipboard(result)

    print(f"✅ Copied to clipboard ({LANG_NAMES[src]} → {LANG_NAMES[dst]}, {tone})\n")
    print("─" * 40)
    print(result)


if __name__ == "__main__":
    main()
