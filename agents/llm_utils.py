import json
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


def get_groq_client() -> Groq:
    """
    Create a Groq client using the local GROQ_API_KEY.

    The key should be stored in a local .env file and should not be committed
    to GitHub.
    """
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    return Groq(api_key=api_key)


def call_groq_json(
    system_message: str,
    user_message: str,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.2,
) -> dict[str, Any]:
    """
    Call Groq/Llama and require a JSON object response.

    This helper centralises the LLM call so Planning, Processing, Ranking, and
    Evidence agents can share one consistent pattern.
    """
    client = get_groq_client()

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=temperature,
    )

    content = completion.choices[0].message.content

    if not content:
        raise ValueError("Groq returned an empty response.")

    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(f"Groq did not return valid JSON: {content}") from error