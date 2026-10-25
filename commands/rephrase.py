#!/usr/bin/env python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Rephrase
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 💬
# @raycast.packageName Local LLM Writing Tools
# @raycast.argument1 { "type": "dropdown", "placeholder": "Audience", "data": [{"title": "Engineering", "value": "engineering"}, {"title": "Non-technical", "value": "non-technical"}, {"title": "Friend", "value": "friend"}, {"title": "Leadership", "value": "leadership"}] }
# @raycast.argument2 { "type": "dropdown", "placeholder": "Tone", "data": [{"title": "Friendly", "value": "friendly"}, {"title": "Neutral", "value": "neutral"}, {"title": "Formal", "value": "formal"}] }
# @raycast.argument3 { "type": "dropdown", "placeholder": "Model", "data": [{"title": "gemma4:e4b-it-qat", "value": "gemma4:e4b-it-qat"}, {"title": "gemma4:e4b", "value": "gemma4:e4b"}] }

# Documentation:
# @raycast.description Rephrase clipboard text for an audience and tone using a local LLM
# @raycast.author Andrew Chernous

import sys

from ollama_client import TONE_HINTS, OllamaError, chat, get_clipboard, set_clipboard

AUDIENCE_HINTS = {
    "engineering": "fellow engineers and technical PMs. Technical terms are fine, no need to explain jargon",
    "non-technical": "non-technical readers. Avoid jargon, explain technical concepts plainly",
    "friend": "a close friend. Casual wording, contractions are welcome",
    "leadership": "senior leadership. Concise, outcome-focused, lead with the takeaway",
}

# Higher temperature than Proofread: rephrasing benefits from varied wording,
# and re-running the hotkey gives the user a different option.
SAMPLING = {"temperature": 1.0, "top_p": 0.95, "top_k": 64}


def build_system_prompt(audience: str, tone: str) -> str:
    return (
        "You are an English editor. Rewrite the user's text following these rules:\n"
        f"- Audience: {AUDIENCE_HINTS[audience]}.\n"
        f"- Tone: {TONE_HINTS[tone]}\n"
        "- Preserve original meaning and approximate length.\n"
        "- Preserve all markdown formatting exactly as in the input: "
        "inline code with backticks (`like this`), fenced code blocks (```), "
        "bold (**word**), italics (*word*), links, lists, and line breaks. "
        "Do not add markdown that wasn't there, do not strip markdown that was.\n"
        "- Do NOT wrap your entire response in a code block or quotes.\n"
        "- Return ONLY the rewritten text. No preamble like 'Here is the corrected version', "
        "no explanations, no trailing commentary."
    )


def main() -> None:
    audience, tone, model = sys.argv[1], sys.argv[2], sys.argv[3]

    source = get_clipboard()
    if not source.strip():
        print("Clipboard is empty. Copy some text first (Cmd+C) and try again.")
        sys.exit(1)

    try:
        result = chat(model, build_system_prompt(audience, tone), source, SAMPLING)
    except OllamaError as e:
        print(f"⚠️  {e}")
        sys.exit(1)

    set_clipboard(result)

    print(f"✅ Copied to clipboard ({audience} / {tone} / {model})\n")
    print("─" * 40)
    print(result)


if __name__ == "__main__":
    main()
