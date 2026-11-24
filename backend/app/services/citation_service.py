"""Check the citations in an AI draft against the policy extracts that were retrieved.

The AI is only shown a few policy passages, so it may cite:
- a policy that was never provided ("internal Compliance policy, page 5"),
- a page of a real policy that was not provided,
- a provided page that has nothing to do with the action it is attached to,
- a regulation or circular number that appears nowhere in the input, or a placeholder
  such as "RBI/2023-24/xx".
Each of these is reported back, and removed from the draft where it is clearly a
citation (in brackets, after "as per"/"as required by", or with a page number).
"""

import re
from pathlib import Path

DOC_SUFFIX = re.compile(r"\b(?:policy|standard|procedure|guidelines?|framework)\b", re.IGNORECASE)
PDF_TOKEN = re.compile(r"\b[\w\-]+\.pdf\b", re.IGNORECASE)
# ", page 2" / " (page 2)" / " p. 2" right after a document name
PAGE_AFTER = re.compile(r"^\s*[,;:]?\s*(\()?\s*(?:page|p\.|pg\.?)\s*(\d+)\s*(?(1)\))", re.IGNORECASE)
# "page 2 of the " right before a document name
PAGE_BEFORE = re.compile(r"\b(?:page|p\.|pg\.?)\s*(\d+)\s+of\s+(?:the\s+)?$", re.IGNORECASE)
CONNECTIVE_BEFORE = re.compile(
    r"(?:,\s*)?\b(?:as\s+required\s+by|as\s+per|per|in\s+line\s+with|according\s+to|aligned\s+with|"
    r"in\s+compliance\s+with|in\s+accordance\s+with|as\s+outlined\s+in|as\s+mandated\s+by|"
    r"as\s+set\s+out\s+in|as\s+stated\s+in|as\s+defined\s+in|under|following|see|refer\s+to)"
    r"\s+(?:(?:the|bank'?s|internal|our)\s+)*$",
    re.IGNORECASE,
)
OPEN_BRACKET_BEFORE = re.compile(r"([(\[])\s*(?:e\.g\.,?|i\.e\.,?|eg,?|for\s+example,?)?\s*$", re.IGNORECASE)
CLOSING = {"(": ")", "[": "]"}

# Regulation-like references (circular numbers, legal sections, placeholders).
REGULATION_PATTERNS = [
    r"\b(?:RBI|SEBI|NPCI|IRDAI|DPSS|DBR|DOR|DoS)\s*/\s*\d{2,4}[\w/.\-]*",
    r"\b(?:RBI|DBR|DOR|DPSS|DoS|CO)\.[A-Za-z.]*\s*No\.?\s*\d[\w/.\-]*",
    r"\bcircular\s*(?:no\.?|number|ref\.?)\s*[:#]?\s*[\w./ -]{0,25}\d[\w/.\-]*",
    r"\b(?:DPSS|DBR|DOR|DoS|DCM|DBS|FIDD)\.[A-Z]{2,}[\w/.\-]*",
    r"\bmaster\s+direction\s*(?:no\.?|number)\s*\S*\d[\w/.\-]*",
    r"\bnotification\s*(?:no\.?|number)\s*\S*\d[\w/.\-]*",
    r"\bsection\s+\d+[A-Z]?(?:\(\w+\))?\s+of\s+the\s+(?!vendor)[A-Z][\w ]*?\b(?:Act|Regulations?|Directions?)\b",
]
PLACEHOLDER = re.compile(r"x{2,}|\.\.\.|<[^>]*>|\[[^\]]*\]", re.IGNORECASE)

NAME_FILLER = {"the", "bank's", "banks", "bank", "internal", "our", "a", "an"}
GENERIC_WORDS = {
    "vendor", "vendors", "policy", "policies", "bank", "banks", "page", "management", "manage",
    "programme", "programmes", "project", "projects", "must", "should", "shall", "required",
    "require", "requires", "ensure", "with", "that", "this", "from", "into", "their", "they",
    "have", "been", "will", "before", "after", "such", "each", "also", "where", "when", "than",
    "them", "these", "those", "only", "under", "within", "about",
    # common verbs and fillers in actions that say nothing about the policy content
    "include", "includes", "including", "implement", "conduct", "establish", "provide",
    "perform", "assign", "regular", "regularly", "update", "review", "process", "processes",
    "clear", "clearly", "immediately", "immediate", "appropriate", "relevant", "other", "more",
    "need", "needed", "needs", "using", "based", "make", "made", "take", "place", "team",
    "teams", "work", "plans", "early", "time", "timely", "accordingly", "necessary",
}
SKIP_FIELDS = {"suggested_category"}
MAX_NAME_WORDS = 6


def _normalise_doc(name: str) -> str:
    name = name.strip()
    if name.lower().endswith(".pdf"):
        name = Path(name).stem
    words = re.sub(r"[_\-]+", " ", name.lower()).split()
    return " ".join(w for w in words if w not in NAME_FILLER)


def _content_keys(text: str) -> set:
    """Meaningful words, cut to 5 letters so 'escalate' and 'escalation' match."""
    words = re.findall(r"[a-z]{4,}", text.lower())
    return {w[:5] for w in words if w not in GENERIC_WORDS}


def _tidy(text: str) -> str:
    text = re.sub(r"\(\s*\)|\[\s*\]", "", text)
    text = re.sub(r"\s+([,.;:)\]])", r"\1", text)
    text = re.sub(r"([,;:])\s*([.;])", r"\2", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip().rstrip(",;:").strip()


def _cut(text: str, start: int, end: int) -> str:
    """Remove text[start:end] with its brackets or leading connective, then tidy."""
    before, after = text[:start], text[end:]
    connective = CONNECTIVE_BEFORE.search(before)
    if connective:
        before = before[: connective.start()]
    bracket = OPEN_BRACKET_BEFORE.search(before)
    if bracket and after.lstrip().startswith(CLOSING[bracket.group(1)]):
        before = before[: bracket.start()]
        after = after.lstrip()[1:]
    return _tidy(before.rstrip() + " " + after.lstrip())


def _is_marked_as_citation(text: str, start: int, has_page: bool) -> bool:
    before = text[:start]
    return has_page or bool(CONNECTIVE_BEFORE.search(before) or OPEN_BRACKET_BEFORE.search(before))


class _Checker:
    def __init__(self, policies: list, user_text: str):
        self.pages = {}  # normalised doc name -> {page: retrieved passage text}
        for p in policies or []:
            doc = _normalise_doc(str(p.get("document", "")))
            page_texts = self.pages.setdefault(doc, {})
            page = p.get("page")
            page_texts[page] = (page_texts.get(page, "") + " " + str(p.get("text", ""))).strip()
        self.doc_words = {w for doc in self.pages for w in doc.split()}
        self.source_text = " ".join(
            [user_text] + [str(p.get("text", "")) for p in policies or []]
        ).lower()
        self.warnings = []

    # ---- policy citations ----

    def _name_tokens(self, text: str, anchor: re.Match) -> list:
        """Name words before a 'Policy' anchor (capitalised or part of a known document name)."""
        tokens = [(anchor.start(), anchor.group(0))]
        cursor = anchor.start()
        for w in reversed(list(re.finditer(r"[A-Za-z][\w'&\-]*", text[:cursor]))):
            if text[w.end():cursor].strip() or len(tokens) > MAX_NAME_WORDS:
                break
            token = w.group(0)
            if not (token[0].isupper() or token.lower() in self.doc_words):
                break
            tokens.insert(0, (w.start(), token))
            cursor = w.start()
        return tokens if len(tokens) > 1 else []  # a bare "policy" is not a named document

    def _candidates(self, text: str) -> list:
        found = [[(m.start(), m.group(0))] for m in PDF_TOKEN.finditer(text)]
        pdf_spans = [(m.start(), m.end()) for m in PDF_TOKEN.finditer(text)]
        for m in DOC_SUFFIX.finditer(text):
            if any(s <= m.start() < e for s, e in pdf_spans):
                continue
            tokens = self._name_tokens(text, m)
            if tokens:
                found.append(tokens)
        return sorted(found)

    def _check_policy(self, text: str, tokens: list):
        """Return (start, end, citation, reason, removable) for a bad citation, else None."""
        end = tokens[-1][0] + len(tokens[-1][1])
        # Match the longest known document name ending at the anchor, so a leading
        # verb such as "Enforce Vendor Management Policy" still matches.
        doc, start = None, tokens[0][0]
        for i in range(len(tokens)):
            candidate = _normalise_doc(" ".join(t for _, t in tokens[i:]))
            if candidate in self.pages:
                doc, start = candidate, tokens[i][0]
                break

        page = None
        after = PAGE_AFTER.match(text[end:])
        if after:
            page, end = int(after.group(2)), end + after.end()
        else:
            before = PAGE_BEFORE.search(text[:start])
            if before:
                page, start = int(before.group(1)), before.start()
        citation = text[start:end].strip(" ()")

        if doc is None:
            removable = _is_marked_as_citation(text, start, page is not None)
            return start, end, citation, "this policy was not among the extracts provided", removable
        if page is None:
            return None
        if page not in self.pages[doc]:
            return start, end, citation, f"page {page} was not among the extracts provided", True
        action = text[:start] + " " + text[end:]
        if not _content_keys(action) & _content_keys(self.pages[doc][page]):
            return start, end, citation, f"the extract from page {page} does not cover this action", True
        return None

    # ---- regulation references ----

    def _check_regulations(self, text: str) -> list:
        problems = []
        for pattern in REGULATION_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                ref = m.group(0).strip().rstrip(".,;")
                if "policy" in ref.lower():
                    continue
                if PLACEHOLDER.search(ref):
                    reason = "placeholder, not a real reference"
                elif ref.lower() not in self.source_text:
                    reason = "not found in the record or the policy extracts"
                else:
                    continue
                problems.append((m.start(), m.start() + len(ref), ref, reason, True))
        return problems

    # ---- cleaning ----

    def _report(self, field, citation, reason, reported):
        if (citation, reason) not in reported:
            reported.add((citation, reason))
            self.warnings.append({"field": field, "citation": citation, "reason": reason})

    def clean_text(self, field: str, text: str) -> str:
        reported = set()
        for _ in range(20):  # each pass removes one citation
            problems = [p for p in (self._check_policy(text, t) for t in self._candidates(text)) if p]
            problems += self._check_regulations(text)
            # Plain mentions ("follow the Change Policy for releases") are reported, not cut.
            for _, _, citation, reason, removable in problems:
                if not removable:
                    self._report(field, citation, reason, reported)
            removable = [p for p in problems if p[4]]
            if not removable:
                break
            start, end, citation, reason, _ = min(removable)
            self._report(field, citation, reason, reported)
            text = _cut(text, start, end)
        return text

    def clean_value(self, field: str, value):
        if isinstance(value, str):
            return self.clean_text(field, value)
        if isinstance(value, list):
            cleaned = [self.clean_text(field, v) if isinstance(v, str) else v for v in value]
            return [v for v in cleaned if not (isinstance(v, str) and not v.strip())]
        return value


def verify_citations(result: dict, policies: list, user_text: str = "") -> tuple:
    """Return (cleaned result, warnings). Unsupported citations are reported and removed."""
    if not isinstance(result, dict):
        return result, []
    checker = _Checker(policies, user_text)
    cleaned = {
        key: value if key in SKIP_FIELDS else checker.clean_value(key, value)
        for key, value in result.items()
    }
    return cleaned, checker.warnings
