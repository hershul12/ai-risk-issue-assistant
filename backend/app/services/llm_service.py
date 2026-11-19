import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)