import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def analyze_risk(description: str) -> dict:
    prompt = f"""You are an expert financial risk analyst working for a bank.
Analyze the text below and return ONLY a JSON object with these keys:
- type: "Risk" or "Issue"
- category: one of Credit, Market, Operational, Liquidity, Fraud, Compliance, Cyber Security, Vendor, Project
- severity: Low, Medium or High
- probability: Low, Medium or High
- mitigation: a short, practical suggestion suitable for a bank

Text: {description}"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.choices[0].message.content or ""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else {"raw_response": text}