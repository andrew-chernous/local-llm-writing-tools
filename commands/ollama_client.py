"""Shared plumbing for the Commands: clipboard I/O and the Ollama chat call.

Stdlib only, on purpose: Raycast launches the Commands with whatever `python3`
is on PATH, so there is no virtualenv to install dependencies into.

This file has no `@raycast` header, so Raycast does not list it as a Command;
the Commands import it as a sibling module.
"""

import json
import subprocess
import urllib.error
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"

# Used by Commands without a Model dropdown (Translate already fills all three
# of Raycast's argument slots). Keep it as the first item of every Model
# dropdown too: Raycast preselects the first item, so the defaults stay aligned.
DEFAULT_MODEL = "gemma4:e4b-it-qat"

# A cold start loads several GB of weights into memory before the first token,
# which can take tens of seconds on a laptop.
REQUEST_TIMEOUT_S = 120

# Keeps the model in memory for back-to-back hotkey presses, then frees it.
KEEP_ALIVE = "5m"

# The Commands return text of roughly the input's length; this leaves headroom
# for long inputs while still capping a model that starts rambling.
MAX_OUTPUT_TOKENS = 2048

# One definition of Tone (output register) shared by Rephrase and Translate.
# "neutral" keeps the source's register rather than meaning "edit lightly",
# so it doesn't overlap with Proofread.
TONE_HINTS = {
    "friendly": (
        "Use a friendly, conversational Slack-style register: warm but professional. "
        "Contractions are welcome. Avoid stiff or overly formal phrasing."
    ),
    "neutral": ("Keep the register of the original text. Don't make it more formal or more casual."),
    "formal": ("Use a formal register suitable for emails, official documents and business communication."),
}


class OllamaError(Exception):
    """Ollama could not produce a usable answer.

    The message is shown to the user as-is, so it must say what to do next
    (start Ollama, pull the model, ...), not just what failed.
    """


def get_clipboard() -> str:
    """Return the clipboard text, decoded as robustly as possible.

    Raycast runs scripts without a locale, so relying on Python's default
    encoding can fall back to ASCII and fail on Cyrillic, em-dashes or emoji.
    Most apps put UTF-8 on the clipboard, but some (legacy Windows-origin
    content, certain Slack copy paths) put CP1251/CP1252 bytes there.
    """
    raw: bytes = subprocess.run(["pbpaste"], capture_output=True, check=True).stdout

    for encoding in ("utf-8", "cp1251", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    # Last resort: show something rather than crash on one bad byte.
    return raw.decode("utf-8", errors="replace")


def set_clipboard(text: str) -> None:
    """Replace the clipboard with `text`, encoded as UTF-8 for the same locale reason as `get_clipboard`."""
    subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)


def chat(model: str, system: str, user_text: str, sampling: dict) -> str:
    """Send one system + user message pair to Ollama and return the reply text.

    `sampling` holds the per-Command temperature/top_p/top_k: Proofread wants
    predictable output, Rephrase and Translate benefit from variety.

    Raises:
        OllamaError: Ollama is not running, the model is not pulled, the call
            timed out, or the model returned nothing. Callers must not touch
            the clipboard in that case.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "stream": False,
        # Disable Gemma 4's reasoning mode: these tasks don't need it, and it
        # eats the token budget that should go to the actual answer.
        "think": False,
        "options": {**sampling, "num_predict": MAX_OUTPUT_TOKENS},
        "keep_alive": KEEP_ALIVE,
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    # HTTPError subclasses URLError, so it must be caught first.
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise OllamaError(f"Model '{model}' is not installed.\nRun: ollama pull {model}") from e
        body = e.read().decode("utf-8", errors="replace")
        raise OllamaError(f"Ollama returned HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise OllamaError(
            f"Ollama is unreachable at {OLLAMA_URL}.\n"
            f"Is it running? Start it with: ollama serve\nReason: {e.reason}"
        ) from e
    except TimeoutError as e:
        raise OllamaError(
            f"Ollama did not answer within {REQUEST_TIMEOUT_S}s. Try a smaller model or shorter text."
        ) from e

    content = data["message"]["content"].strip()
    if not content:
        raise OllamaError("Model returned an empty response. Clipboard left unchanged.")
    return content
