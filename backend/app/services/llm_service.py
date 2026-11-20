import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)

client = OpenAI(
    # A placeholder lets the server start without a key; only /suggest then fails.
    api_key=os.getenv("GROQ_API_KEY") or "missing-key",
    base_url="https://api.groq.com/openai/v1",
)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def suggest_text(title: str, description: str, category: str | None = None,
                 similar: list | None = None) -> dict:
    examples = "\n".join(
        f"- {c['description']} -> mitigation: {c['mitigation']}" for c in (similar or [])
    ) or "none"
    prompt = f"""You are an expert project risk analyst in a bank programme office.
Improve the record below. Return ONLY a JSON object with these keys:
- standardised_description: one or two clear sentences covering cause, event and impact
- suggested_category: one of Schedule, Budget, Scope, Resource, Technical, Vendor, Compliance, Security
- suggested_mitigation: a short, practical mitigation or resolution plan
- follow_up_actions: a list of exactly 3 short follow-up actions

Title: {title or "not given"}
Category given by the user: {category or "not given"}
Description: {description}

Similar past risks and how they were handled (use only if relevant):
{examples}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        timeout=30,
    )
    text = response.choices[0].message.content or ""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else {"raw_response": text}