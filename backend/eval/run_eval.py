"""Evaluate RiskPilot's "Draft with AI" (/suggest) against a fixed set of cases.

This calls the REAL Azure OpenAI through a running backend, so it is not part of
pytest or CI. Usage (from the project root, with the backend running):

    venv\\Scripts\\python.exe backend/eval/run_eval.py --policy path/to/Vendor_Management_Policy.pdf

It writes docs/evaluation.md. Re-running overwrites that file, including the
"Reviewer accepted" column, so copy your review notes out first.
"""

import argparse
import json
import math
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = Path(__file__).resolve().parent / "cases.json"
OUT_PATH = ROOT / "docs" / "evaluation.md"

STRUCTURED_FIELDS = [
    "standardised_description", "suggested_category", "suggested_mitigation",
    "follow_up_actions", "cause", "potential_impact", "warning_indicators",
    "preventive_actions", "corrective_actions", "contingency_plan",
]

# Patterns that look like a specific regulation reference (circular numbers, legal
# sections). The test text never contains these, so any match is likely invented.
REGULATION_PATTERNS = [
    r"\b(?:RBI|SEBI|NPCI|IRDAI|DPSS|DBR|DOR|DoS)\s*/\s*\d{2,4}",
    r"\b(?:RBI|DBR|DOR|DPSS|DoS|CO)\.[A-Za-z.]*\s*No\.?\s*\d",
    r"\bcircular\s*(?:no\.?|number|ref\.?)\s*[:#]?\s*[\w./ -]{0,25}\d",
    r"\b(?:DPSS|DBR|DOR|DoS|DCM|DBS|FIDD)\.[A-Z]{2,}",
    r"\bmaster\s+direction\s*(?:no\.?|number)\s*\S*\d",
    r"\bnotification\s*(?:no\.?|number)\s*\S*\d",
    r"\bsection\s+\d+[A-Z]?(?:\(\w+\))?\s+of\s+the\s+(?!vendor)[A-Z][\w ]*\b(?:Act|Regulations?|Directions?)\b",
]


# ---------- helpers ----------

def as_list(value):
    if isinstance(value, list):
        return [v if isinstance(v, str) else json.dumps(v) for v in value]
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def as_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(as_list(value))
    return ""


def is_present(value):
    return bool(as_text(value).strip())


def policy_names(document):
    stem = Path(document).stem
    return {stem.lower(), stem.replace("_", " ").lower(), document.lower()}


def cites_page(text, document, page):
    text_l = text.lower()
    named = any(name in text_l for name in policy_names(document))
    page_hit = re.search(rf"\b(?:page|p\.|pg\.?)\s*{page}\b", text_l) is not None
    return named and page_hit


def regulation_refs(text):
    return sorted({ref["match"] for ref in regulation_refs_in_context({"text": text})})


def regulation_refs_in_context(fields):
    """Find regulation-like references in each field, with surrounding text for the reviewer."""
    found = []
    for name, value in fields.items():
        text = as_text(value)
        for pattern in REGULATION_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                snippet = m.group(0).strip()
                if "policy" in snippet.lower():
                    continue
                start, end = max(m.start() - 70, 0), min(m.end() + 70, len(text))
                context = ("..." if start else "") + text[start:end].strip() + ("..." if end < len(text) else "")
                found.append({"field": name, "match": snippet, "context": " ".join(context.split())})
    unique = {(f["field"], f["context"]): f for f in found}
    return list(unique.values())


def pages_cited(text):
    return sorted({int(n) for n in re.findall(r"\b(?:page|p\.|pg\.?)\s*(\d+)\b", text, re.IGNORECASE)})


def shorten(text, limit=180):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def mark(ok):
    if ok is None:
        return "n/a"
    return "yes" if ok else "**no**"


def pct(passed, total):
    return f"{passed}/{total} ({passed / total:.0%})" if total else "n/a"


def p95(values):
    ordered = sorted(values)
    rank = math.ceil(0.95 * len(ordered))  # nearest-rank method
    return ordered[max(rank, 1) - 1]


# ---------- backend calls ----------

def ensure_policy(client, policy_path, expected_name):
    uploaded = {p["name"] for p in client.get("/policies").json()}
    if expected_name in uploaded:
        return f"`{expected_name}` was already uploaded; not uploaded again."
    if not policy_path:
        sys.exit(f"{expected_name} is not uploaded. Pass --policy <path to the PDF>.")
    path = Path(policy_path)
    if not path.is_file():
        sys.exit(f"Policy PDF not found: {path}")
    with path.open("rb") as fh:
        res = client.post(
            "/policies",
            headers={"X-Role": "Project Manager"},
            files={"file": (expected_name, fh, "application/pdf")},
        )
    if res.status_code != 201:
        sys.exit(f"Policy upload failed ({res.status_code}): {res.text}")
    info = res.json()
    return f"Uploaded `{expected_name}` for this run ({info['pages']} pages, {info['passages']} passages)."


def run_case(client, case):
    start = time.perf_counter()
    try:
        res = client.post("/suggest", json={"title": case["title"], "description": case["description"]})
        elapsed = time.perf_counter() - start
        body = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
        error = None if res.status_code == 200 else f"HTTP {res.status_code}: {body.get('detail', res.text)[:120]}"
    except httpx.HTTPError as e:
        elapsed = time.perf_counter() - start
        body, error = {}, f"{type(e).__name__}"

    result = body.get("result") or {}
    similar = body.get("similar") or []
    policies = body.get("policies") or []
    citation_warnings = body.get("citation_warnings") or []
    returned_category = result.get("suggested_category")

    allowed = {case.get("expected_category"), *case.get("acceptable_categories", [])} - {None}
    category_ok = (returned_category in allowed) if case.get("expected_category") else None
    exact_category = (returned_category == case.get("expected_category")) if case.get("expected_category") else None

    missing = [f for f in STRUCTURED_FIELDS if not is_present(result.get(f))]
    fields_ok = not error and not missing

    page = case.get("expected_policy_page")
    actions_text = " ".join(as_list(result.get("preventive_actions")) + as_list(result.get("corrective_actions")))
    if page:
        retrieved_ok = any(p.get("page") == page for p in policies)
        cited_ok = cites_page(actions_text, POLICY_DOCUMENT, page)
    else:
        retrieved_ok = cited_ok = None

    no_match_ok = (not similar and not policies) if case["type"] == "no_match" else None

    all_text = " ".join(as_text(v) for v in result.values())
    reg_context = regulation_refs_in_context(result)
    reg_refs = sorted({r["match"] for r in reg_context})
    cited_pages = pages_cited(actions_text + " " + as_text(result.get("suggested_mitigation")))
    forbidden_hits = [p for p in case.get("forbidden_phrases", []) if re.search(rf"\b{re.escape(p)}\b", all_text)]
    if case["type"] == "adversarial":
        adversarial_ok = fields_ok and not reg_refs and not forbidden_hits and bool(category_ok)
    else:
        adversarial_ok = None

    return {
        "case": case,
        "error": error,
        "seconds": elapsed,
        "similar_categories": [s.get("category", "?") for s in similar],
        "policy_pages": [f"p{p.get('page')}" for p in policies],
        "returned_category": returned_category or "-",
        "category_ok": category_ok,
        "exact_category": exact_category,
        "missing": missing,
        "fields_ok": fields_ok,
        "retrieved_ok": retrieved_ok,
        "cited_ok": cited_ok,
        "no_match_ok": no_match_ok,
        "reg_refs": reg_refs,
        "reg_context": reg_context,
        "cited_pages": cited_pages,
        "citation_warnings": citation_warnings,
        "forbidden_hits": forbidden_hits,
        "adversarial_ok": adversarial_ok,
        "mitigation": as_text(result.get("suggested_mitigation")),
        "preventive": as_list(result.get("preventive_actions")),
        "corrective": as_list(result.get("corrective_actions")),
        "raw": result.get("raw_response"),
    }


# ---------- report ----------

def build_report(rows, base_url, policy_note, started):
    in_scope = [r for r in rows if r["case"]["type"] == "in_scope"]
    with_page = [r for r in rows if r["case"].get("expected_policy_page")]
    no_match = [r for r in rows if r["case"]["type"] == "no_match"]
    adversarial = [r for r in rows if r["case"]["type"] == "adversarial"]
    ai_rows = [r for r in rows if not r["error"]]
    times = [r["seconds"] for r in rows]

    def count(items, key):
        return sum(1 for r in items if r[key])

    lines = [
        "# AI Evaluation: Draft with AI",
        "",
        "## How to run",
        "",
        "1. Start the backend with a valid `.env` (Azure OpenAI settings): "
        "`cd backend` then `uvicorn app.main:app --reload`.",
        "2. From the project root run:",
        "   ```",
        "   venv\\Scripts\\python.exe backend/eval/run_eval.py --policy data/sample_policies/Vendor_Management_Policy.pdf",
        "   ```",
        "   Options: `--base-url` (default `http://127.0.0.1:8000`). The policy is uploaded only if it is not already there.",
        "3. Fill in the **Reviewer accepted (Y/N)** column below.",
        "",
        "> This calls the real Azure OpenAI and costs tokens. It is not part of pytest or CI. "
        "Re-running overwrites this file, including the reviewer column.",
        "",
        "Test cases: `backend/eval/cases.json`. Cases are sent without a category, so the AI must choose one.",
        "",
        "## Run details",
        "",
        f"- Date: {started:%Y-%m-%d %H:%M}",
        f"- Backend: {base_url}",
        f"- Policy: {policy_note}",
        f"- Cases: {len(rows)} ({len(in_scope)} in scope, {len(no_match)} no-match, {len(adversarial)} adversarial)",
        f"- Request errors: {sum(1 for r in rows if r['error'])}",
        "",
        "## Summary",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Category acceptable (in scope + adversarial) | {pct(count(in_scope + adversarial, 'category_ok'), len(in_scope + adversarial))} |",
        f"| Category exactly as expected (in scope) | {pct(count(in_scope, 'exact_category'), len(in_scope))} |",
        f"| All structured fields present (all cases) | {pct(count(rows, 'fields_ok'), len(rows))} |",
        f"| Expected policy page retrieved | {pct(count(with_page, 'retrieved_ok'), len(with_page))} |",
        f"| Expected policy page cited in preventive/corrective actions | {pct(count(with_page, 'cited_ok'), len(with_page))} |",
        f"| No-match: no similar risks and no policies returned | {pct(count(no_match, 'no_match_ok'), len(no_match))} |",
        f"| Adversarial: stayed a normal assessment | {pct(count(adversarial, 'adversarial_ok'), len(adversarial))} |",
        f"| No regulation numbers flagged in the final draft (all AI replies) | {pct(sum(1 for r in ai_rows if not r['reg_refs']), len(ai_rows))} |",
        f"| Drafts with no unsupported citations from the AI | {pct(sum(1 for r in ai_rows if not r['citation_warnings']), len(ai_rows))} |",
        f"| Unsupported citations caught by the backend check | {sum(len(r['citation_warnings']) for r in rows)} |",
        f"| Average response time | {statistics.mean(times):.1f} s |",
        f"| p95 response time | {p95(times):.1f} s |",
        "",
        "## Results",
        "",
        "Similar = categories of the similar past risks retrieved. Policy = pages of policy passages retrieved.",
        "",
        "Pages cited = every policy page the draft cites (mitigation, preventive and corrective actions); "
        "a page not in the Policy column was cited without being retrieved.",
        "",
        "All checks run on the draft the user sees, after the backend has removed unsupported citations. "
        "Citations removed = what the backend check caught in the AI's raw reply.",
        "",
        "| ID | Type | Time (s) | Similar | Policy | Expected cat. | AI cat. | Cat. OK | Fields | Exp. page | Page retrieved | Page cited | Pages cited | No-match OK | Adversarial OK | Reg. refs flagged | Citations removed | Mitigation (shortened) | Reviewer accepted (Y/N) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        c = r["case"]
        fields = "error: " + r["error"] if r["error"] else ("all" if r["fields_ok"] else "missing " + ", ".join(r["missing"]))
        lines.append("| " + " | ".join(cell(v) for v in [
            c["id"],
            c["type"].replace("_", " "),
            f"{r['seconds']:.1f}",
            ", ".join(r["similar_categories"]) or "none",
            ", ".join(r["policy_pages"]) or "none",
            c.get("expected_category") or "-",
            r["returned_category"],
            mark(r["category_ok"]),
            fields,
            c.get("expected_policy_page") or "-",
            mark(r["retrieved_ok"]),
            mark(r["cited_ok"]),
            ", ".join(f"p{p}" for p in r["cited_pages"]) or "none",
            mark(r["no_match_ok"]),
            mark(r["adversarial_ok"]),
            "; ".join(r["reg_refs"] + [f"forbidden: {p}" for p in r["forbidden_hits"]]) or "none",
            "; ".join(w.get("citation", "?") for w in r["citation_warnings"]) or "none",
            shorten(r["mitigation"] or r["raw"] or "-"),
            "",
        ]) + " |")

    lines += ["", "## Draft details for review", ""]
    for r in rows:
        c = r["case"]
        lines += [f"### {c['id']}: {c['title']}", "", f"**Input:** {c['description']}", ""]
        if r["error"]:
            lines += [f"**Error:** {r['error']}", ""]
            continue
        lines.append(f"**Mitigation:** {shorten(r['mitigation'], 400) or '-'}")
        lines.append("")
        if r["preventive"]:
            lines.append("**Preventive actions:**")
            lines += [f"- {shorten(a, 250)}" for a in r["preventive"]]
            lines.append("")
        if r["corrective"]:
            lines.append("**Corrective actions:**")
            lines += [f"- {shorten(a, 250)}" for a in r["corrective"]]
            lines.append("")
        if r["citation_warnings"]:
            lines.append("**Citations removed by the backend check:**")
            lines += [f"- `{w.get('field')}`: {w.get('citation')} ({w.get('reason')})" for w in r["citation_warnings"]]
            lines.append("")
        if r["reg_context"]:
            lines.append("**Flagged regulation-like references (check whether invented):**")
            lines += [f"- `{f['field']}`: \"{f['context']}\"" for f in r["reg_context"]]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


POLICY_DOCUMENT = "Vendor_Management_Policy.pdf"


def main():
    global POLICY_DOCUMENT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--policy", help="Path to the sample policy PDF (uploaded only if missing)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    spec = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    POLICY_DOCUMENT = spec.get("policy_document", POLICY_DOCUMENT)
    started = datetime.now()

    with httpx.Client(base_url=args.base_url, timeout=120) as client:
        try:
            client.get("/health").raise_for_status()
        except httpx.HTTPError as e:
            sys.exit(f"Backend not reachable at {args.base_url}: {e}")
        policy_note = ensure_policy(client, args.policy, POLICY_DOCUMENT)

        rows = []
        for case in spec["cases"]:
            print(f"{case['id']:7} ...", end=" ", flush=True)
            row = run_case(client, case)
            print(f"{row['seconds']:.1f}s {'ERROR ' + row['error'] if row['error'] else row['returned_category']}")
            rows.append(row)

    OUT_PATH.write_text(build_report(rows, args.base_url, policy_note, started), encoding="utf-8")
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
