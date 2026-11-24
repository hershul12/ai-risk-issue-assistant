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
BASELINE_PATH = Path(__file__).resolve().parent / "baseline.json"
BASELINE_RESULTS_PATH = Path(__file__).resolve().parent / "baseline_results.md"
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
    # found=false means the backend judged the text out of scope and returned no draft.
    found = None if error else body.get("found", True) is not False
    expect_draft = case["type"] != "no_match"

    allowed = {case.get("expected_category"), *case.get("acceptable_categories", [])} - {None}
    category_ok = (returned_category in allowed) if case.get("expected_category") else None
    exact_category = (returned_category == case.get("expected_category")) if case.get("expected_category") else None

    missing = [f for f in STRUCTURED_FIELDS if not is_present(result.get(f))]
    fields_ok = (not error and not missing) if expect_draft else None
    accepted_ok = bool(found) if expect_draft else None

    page = case.get("expected_policy_page")
    actions_text = " ".join(as_list(result.get("preventive_actions")) + as_list(result.get("corrective_actions")))
    if page:
        retrieved_ok = any(p.get("page") == page for p in policies)
        cited_ok = cites_page(actions_text, POLICY_DOCUMENT, page)
    else:
        retrieved_ok = cited_ok = None

    # A no-match case passes only on the fallback: found=false with nothing retrieved or drafted.
    if case["type"] == "no_match":
        no_match_ok = found is False and not similar and not policies and not any(
            is_present(result.get(f)) for f in STRUCTURED_FIELDS
        )
    else:
        no_match_ok = None

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
        "found": found,
        "message": body.get("message", ""),
        "accepted_ok": accepted_ok,
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
        "cause": as_text(result.get("cause")),
        "potential_impact": as_text(result.get("potential_impact")),
        "warning_indicators": as_list(result.get("warning_indicators")),
        "preventive": as_list(result.get("preventive_actions")),
        "corrective": as_list(result.get("corrective_actions")),
        "contingency_plan": as_text(result.get("contingency_plan")),
        "follow_up": as_list(result.get("follow_up_actions")),
        # sample_risks.csv has no title column, so the risk is identified by id + description.
        "similar_used": [
            f"#{s.get('id', '?')} ({s.get('category', '?')}): {s.get('description', '')}" for s in similar
        ],
        "policies_used": [
            f"{p.get('document', '?')}, page {p.get('page', '?')}: {p.get('text', '')}" for p in policies
        ],
        "raw": result.get("raw_response"),
    }


# ---------- report ----------

SUMMARY_LABELS = [
    ("category_ok", "Category acceptable (in scope + adversarial)"),
    ("category_exact", "Category exactly as expected (in scope)"),
    ("accepted", "Genuine cases drafted, not wrongly rejected (in scope + adversarial)"),
    ("fields", "All structured fields present (in scope + adversarial)"),
    ("page_retrieved", "Expected policy page retrieved"),
    ("page_cited", "Expected policy page cited in preventive/corrective actions"),
    ("no_match", "No-match: fallback (found=false, nothing retrieved or drafted)"),
    ("adversarial", "Adversarial: stayed a normal assessment"),
    ("no_reg_refs", "No regulation numbers flagged in the final draft"),
    ("no_unsupported", "Drafts with no unsupported citations from the AI"),
    ("citations_caught", "Unsupported citations caught by the backend check"),
    ("avg_time", "Average response time"),
    ("p95_time", "p95 response time"),
]


def summarise(rows):
    in_scope = [r for r in rows if r["case"]["type"] == "in_scope"]
    with_page = [r for r in rows if r["case"].get("expected_policy_page")]
    no_match = [r for r in rows if r["case"]["type"] == "no_match"]
    adversarial = [r for r in rows if r["case"]["type"] == "adversarial"]
    genuine = in_scope + adversarial
    drafts = [r for r in rows if not r["error"] and r["found"]]
    times = [r["seconds"] for r in rows]

    def count(items, key):
        return sum(1 for r in items if r[key])

    return {
        "category_ok": pct(count(genuine, "category_ok"), len(genuine)),
        "category_exact": pct(count(in_scope, "exact_category"), len(in_scope)),
        "accepted": pct(count(genuine, "accepted_ok"), len(genuine)),
        "fields": pct(count(genuine, "fields_ok"), len(genuine)),
        "page_retrieved": pct(count(with_page, "retrieved_ok"), len(with_page)),
        "page_cited": pct(count(with_page, "cited_ok"), len(with_page)),
        "no_match": pct(count(no_match, "no_match_ok"), len(no_match)),
        "adversarial": pct(count(adversarial, "adversarial_ok"), len(adversarial)),
        "no_reg_refs": pct(sum(1 for r in drafts if not r["reg_refs"]), len(drafts)),
        "no_unsupported": pct(sum(1 for r in drafts if not r["citation_warnings"]), len(drafts)),
        "citations_caught": str(sum(len(r["citation_warnings"]) for r in rows)),
        "avg_time": f"{statistics.mean(times):.1f} s",
        "p95_time": f"{p95(times):.1f} s",
    }


def before_fixes_section(summary):
    """Earlier runs from baseline.json, side by side with this run, plus the original results."""
    if not BASELINE_PATH.is_file():
        return []
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    runs = baseline["runs"]
    lines = [
        "## Before fixes",
        "",
        baseline.get("intro", ""),
        "",
        "| Check | " + " | ".join(r["label"] for r in runs) + " | This run |",
        "|---|" + "---|" * (len(runs) + 1),
    ]
    for key, label in SUMMARY_LABELS:
        values = [r["summary"].get(key, "n/a") for r in runs]
        lines.append(f"| {label} | " + " | ".join(values) + f" | {summary[key]} |")
    lines.append("")
    for r in runs:
        if r.get("findings"):
            lines += [f"**{r['label']}:**", ""] + [f"- {f}" for f in r["findings"]] + [""]
    if BASELINE_RESULTS_PATH.is_file():
        lines += [BASELINE_RESULTS_PATH.read_text(encoding="utf-8").strip(), ""]
    return lines


def build_report(rows, base_url, policy_note, started):
    in_scope = [r for r in rows if r["case"]["type"] == "in_scope"]
    no_match = [r for r in rows if r["case"]["type"] == "no_match"]
    adversarial = [r for r in rows if r["case"]["type"] == "adversarial"]
    summary = summarise(rows)

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
        "Earlier runs for the \"Before fixes\" section: `backend/eval/baseline.json` and `baseline_results.md`.",
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
        *[f"| {label} | {summary[key]} |" for key, label in SUMMARY_LABELS],
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
        "Found = whether the backend treated the text as in scope and drafted it (no = fallback message).",
        "",
        "| ID | Type | Time (s) | Found | Similar | Policy | Expected cat. | AI cat. | Cat. OK | Fields | Exp. page | Page retrieved | Page cited | Pages cited | No-match OK | Adversarial OK | Reg. refs flagged | Citations removed | Mitigation (shortened) | Reviewer accepted (Y/N) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        c = r["case"]
        if r["error"]:
            fields = "error: " + r["error"]
        elif r["found"] is False:
            fields = "fallback"
        else:
            fields = "all" if not r["missing"] else "missing " + ", ".join(r["missing"])
        lines.append("| " + " | ".join(cell(v) for v in [
            c["id"],
            c["type"].replace("_", " "),
            f"{r['seconds']:.1f}",
            "-" if r["found"] is None else ("yes" if r["found"] else "no"),
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
            shorten(r["mitigation"] or r["raw"] or (f"Fallback: {r['message']}" if r["found"] is False else "-")),
            "",
        ]) + " |")
    lines.append("")
    lines += before_fixes_section(summary)

    lines += ["", "## Draft details for review", ""]
    for r in rows:
        c = r["case"]
        lines += [f"### {c['id']}: {c['title']}", "", f"**Input:** {c['description']}", ""]
        if r["error"]:
            lines += [f"**Error:** {r['error']}", ""]
            continue
        if r["found"] is False:
            lines += [f"**Fallback (no draft):** {r['message']}", ""]
            continue
        lines.append("**Similar risks used:**" + ("" if r["similar_used"] else " none"))
        lines += [f"- {shorten(s, 200)}" for s in r["similar_used"]]
        lines.append("")
        lines.append("**Policy passages used:**" + ("" if r["policies_used"] else " none"))
        lines += [f"- {shorten(p, 300)}" for p in r["policies_used"]]
        lines.append("")
        lines.append(f"**Cause:** {shorten(r['cause'], 300) or '-'}")
        lines.append("")
        lines.append(f"**Potential impact:** {shorten(r['potential_impact'], 300) or '-'}")
        lines.append("")
        if r["warning_indicators"]:
            lines.append("**Warning indicators:**")
            lines += [f"- {shorten(a, 200)}" for a in r["warning_indicators"]]
            lines.append("")
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
        lines.append(f"**Contingency plan:** {shorten(r['contingency_plan'], 300) or '-'}")
        lines.append("")
        if r["follow_up"]:
            lines.append("**Follow-up actions:**")
            lines += [f"- {shorten(a, 200)}" for a in r["follow_up"]]
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
