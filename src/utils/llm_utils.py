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
Read the user's raw message and return only JSON matching the provided schema.

Rules:
- Determine the user's intent from the full meaning of the message.
- If the user wants music to start or queue, use action "play".
- For play requests, put a YouTube-search-friendly query into "query".
- Keep artist names, song names, and playlist names in their original language whenever possible.
- Remove command filler words such as "play", "please", or "help me" from "query".
- Do not translate names into another language.
- Do not paraphrase into full sentences.
- Do not invent details that the user did not provide.
- Prefer short keyword-style queries that are likely to work well in YouTube search.
- For pause, resume, skip, stop, and now_playing, return an empty query string.
- If the message is not clearly a music control request, return {"action":"none","query":""}.
- Never answer conversationally.
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
