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

CATEGORIES = {"Schedule", "Budget", "Scope", "Resource",
              "Technical", "Vendor", "Compliance", "Security"}


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


def extract_items(text: str) -> list:
    prompt = f"""You are an expert project risk analyst in a bank programme office.
Read the email or meeting notes below and find every project risk (something that
might go wrong) and issue (something that has already gone wrong).
Return ONLY a JSON object with one key "items": a list of at most 10 objects with these keys:
- title: a short title, under 80 characters
- description: one or two clear sentences covering cause, event and impact
- item_type: "Risk" or "Issue"
- category: one of Schedule, Budget, Scope, Resource, Technical, Vendor, Compliance, Security
- suggested_mitigation: a short, practical mitigation or resolution plan
If there are no risks or issues, return {{"items": []}}.

Text:
{text}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        timeout=60,
    )
    reply = response.choices[0].message.content or ""
    match = re.search(r"\{.*\}", reply, re.DOTALL)
    data = json.loads(match.group(0)) if match else {}

    items = []
    for raw in data.get("items", []):
        if not isinstance(raw, dict):
            continue
        title = str(raw.get("title", "")).strip()[:200]
        description = str(raw.get("description", "")).strip()
        if len(title) < 3 or len(description) < 5:
            continue
        item_type = raw.get("item_type") if raw.get("item_type") in ("Risk", "Issue") else "Risk"
        category = raw.get("category") if raw.get("category") in CATEGORIES else "Schedule"
        items.append({
            "title": title,
            "description": description,
            "item_type": item_type,
            "category": category,
            "suggested_mitigation": str(raw.get("suggested_mitigation", "")).strip(),
        })
    return items[:10]