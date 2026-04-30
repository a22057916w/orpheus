import json
from dataclasses import dataclass

import requests

from src import config


ACTION_SCHEMA = {
    "name": "music_bot_intent",
    "schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["play", "pause", "resume", "skip", "stop", "now_playing", "none"],
            },
            "query": {
                "type": "string",
            },
        },
        "required": ["action", "query"],
        "additionalProperties": False,
    },
    "strict": True,
}

SYSTEM_PROMPT = """
You are an intent classifier for a Discord music bot.
Return only JSON matching the schema.

Rules:
- Determine intent from the full message.
- Use one action: play, pause, resume, skip, stop, now_playing, or none.
- For play, make query a short YouTube-friendly music search.
- Keep song, artist, and playlist names in the original language.
- Remove filler words like play, please, or help me.
- Do not translate, paraphrase, or invent details.
- If the user describes a show, game, or movie moment, target the music instead of the clip.
- Add OST, BGM, soundtrack, or theme only when helpful for finding the music.
- For non-play actions, use an empty query.
- If it is not clearly a music command, return {"action":"none","query":""}.
""".strip()


@dataclass
class LLMCommand:
    action: str
    query: str = ""


def is_llm_enabled() -> bool:
    return bool(config.OPENAI_API_KEY and config.OPENAI_MODEL)


def parse_music_request(content: str) -> LLMCommand | None:
    if not is_llm_enabled():
        print("LLM DEBUG: OpenAI integration is disabled because OPENAI_API_KEY or OPENAI_MODEL is missing.")
        return None

    print(f"LLM DEBUG: Parsing message -> {content}")
    print(f"LLM DEBUG: Sending request -> model={config.OPENAI_MODEL}, base_url={config.OPENAI_BASE_URL}")

    try:
        response = requests.post(
            f"{config.OPENAI_BASE_URL.rstrip('/')}/responses",
            headers={
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.OPENAI_MODEL,
                "input": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": ACTION_SCHEMA["name"],
                        "schema": ACTION_SCHEMA["schema"],
                        "strict": ACTION_SCHEMA["strict"],
                    }
                },
            },
            timeout=20,
        )
        print(f"LLM DEBUG: Response received -> status_code={response.status_code}")
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"LLM DEBUG: Request failed -> {exc}")
        return None

    try:
        payload = response.json()
    except ValueError as exc:
        print(f"LLM DEBUG: Failed to decode JSON response -> {exc}")
        print(f"LLM DEBUG: Raw response text -> {response.text}")
        return None

    output = _extract_output_text(payload)
    if not output:
        print(f"LLM DEBUG: No output_text found in payload -> {payload}")
        return None

    print(f"LLM DEBUG: Raw model output -> {output}")

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        print(f"LLM DEBUG: Failed to parse output JSON -> {exc}")
        return None

    command = LLMCommand(
        action=parsed.get("action", "none"),
        query=parsed.get("query", ""),
    )
    print(f"LLM DEBUG: Parsed command -> action={command.action}, query={command.query}")
    return command


def _extract_output_text(payload: dict) -> str | None:
    if payload.get("output_text"):
        return payload["output_text"]

    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if text:
                return text

    return None
