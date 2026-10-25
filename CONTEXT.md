# Local LLM Writing Tools

A set of hotkey commands that take text from the clipboard, run it through a local LLM, and put the result back on the clipboard. The text never leaves the machine.

## Commands

**Command**:
One hotkey action the user runs. Each Command takes the clipboard text, transforms it in one way, and writes the result back to the clipboard. There are three: Rephrase, Proofread, Translate.
_Avoid_: Script, tool, action

**Rephrase**:
A Command that rewrites the text for a chosen Audience and Tone. It may change wording and sentence structure; it must keep the meaning.
_Avoid_: Rewrite, paraphrase

**Proofread**:
A Command that fixes only mistakes (spelling, grammar, articles, word order, punctuation) and keeps the author's voice and word choice, even where a sentence could be phrased better.
_Avoid_: Spell check, grammar check, correct

**Translate**:
A Command that renders the text from the Source Language into the Target Language in the chosen Tone.

## Command options

**Tone**:
The register of the output: Friendly, Neutral or Formal. Neutral means the output keeps the register of the source text. Rephrase and Translate share one definition of Tone.
_Avoid_: Style, voice, mood

**Audience**:
The reader that Rephrase writes for: Engineering, Non-technical, Friend or Leadership. Audience decides vocabulary and emphasis; Tone decides register.
_Avoid_: Reader, target

**Level**:
The CEFR language level (B1, B2 or B1-B2) that Proofread must not go above. Proofread keeps the text at this level so the result still sounds like a non-native author.
_Avoid_: Difficulty, complexity

**Depth**:
Whether Proofread returns only the corrected text (Fix only) or also returns Notes (Fix + explain).

**Notes**:
The short list of the main corrections, each written as "what was wrong, what it became, why". Notes are shown to the user and never copied to the clipboard.
_Avoid_: Explanation, diff, changelog

**Source Language** / **Target Language**:
The language Translate reads from (or Auto-detect) and the language it writes to. The two must be different.

## Runtime

**Model**:
The local Ollama model a Command runs on. Each Command has a default Model; Rephrase and Proofread let the user pick from a list of Models that have been tested.
_Avoid_: Engine, LLM (when meaning a specific model)
