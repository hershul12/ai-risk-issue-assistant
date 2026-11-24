from app.services.citation_service import verify_citations

VMP = "Vendor_Management_Policy.pdf"
POLICIES = [
    {"document": VMP, "page": 1, "text": (
        "Every critical vendor must pass an annual information security audit. If a vendor fails "
        "a security audit, the vendor must submit a written remediation plan within 15 working days."
    )},
    {"document": VMP, "page": 2, "text": (
        "If a vendor delays a deliverable that is on the programme's critical path, the Project "
        "Manager must escalate to the vendor account manager within 3 working days."
    )},
]


def clean(field_value, policies=POLICIES, user_text=""):
    result, warnings = verify_citations({"preventive_actions": field_value}, policies, user_text)
    return result["preventive_actions"], warnings


def test_keeps_valid_citation():
    text = "Require a written remediation plan within 15 working days (Vendor_Management_Policy.pdf, page 1)"
    out, warnings = clean([text])
    assert out == [text]
    assert warnings == []


def test_keeps_valid_citation_with_spaces_and_leading_verb():
    text = "Escalate to the vendor account manager as required by Vendor Management Policy, page 2."
    out, warnings = clean(text)
    assert out == text
    assert warnings == []


def test_removes_policy_that_was_not_provided():
    out, warnings = clean(
        "Include reporting requirements in all runbooks (as required by internal Compliance policy, page 5)."
    )
    assert out == "Include reporting requirements in all runbooks."
    assert warnings[0]["citation"] == "Compliance policy, page 5"
    assert "not among the extracts" in warnings[0]["reason"]


def test_removes_page_that_was_not_retrieved():
    out, warnings = clean("Mask customer data before sharing it, per Vendor Management Policy, page 3.")
    assert out == "Mask customer data before sharing it."
    assert "page 3 was not among" in warnings[0]["reason"]


def test_square_bracket_citations_are_kept_or_removed_cleanly():
    good = "Submit a written remediation plan within 15 working days [Vendor_Management_Policy.pdf, page 1]."
    out, warnings = clean([good, "Hold a post-incident review with the vendor [Vendor_Management_Policy.pdf, page 1]."])
    assert out == [good, "Hold a post-incident review with the vendor."]
    assert len(warnings) == 1


def test_removes_page_that_does_not_cover_the_action():
    out, warnings = clean("Include fee escalation caps in contracts (Vendor_Management_Policy.pdf, page 1)")
    assert out == "Include fee escalation caps in contracts"
    assert "does not cover this action" in warnings[0]["reason"]


def test_any_citation_is_removed_when_no_policies_were_retrieved():
    out, warnings = clean("Restrict vendor access as per the Vendor Management Policy, page 1.", policies=[])
    assert out == "Restrict vendor access."
    assert len(warnings) == 1


def test_plain_mention_of_unknown_policy_is_reported_not_cut():
    text = "Follow the Change Management Policy for all batch releases."
    out, warnings = clean(text)
    assert out == text
    assert warnings[0]["citation"] == "Change Management Policy"


def test_removes_regulation_placeholder():
    out, warnings = clean("Add dual approval during design (aligned with RBI/2023-24/xx).")
    assert out == "Add dual approval during design."
    assert warnings[0]["citation"] == "RBI/2023-24/xx"
    assert "placeholder" in warnings[0]["reason"]


def test_removes_invented_circular_number():
    out, warnings = clean("Update controls as per RBI/2022-23/105 before go-live.")
    assert out == "Update controls before go-live."
    assert "not found" in warnings[0]["reason"]


def test_keeps_regulation_given_by_the_user():
    text = "Map the changes required by RBI/2022-23/105 to the design."
    out, warnings = clean(text, user_text="The new circular RBI/2022-23/105 changes payment limits.")
    assert out == text
    assert warnings == []


def test_list_items_emptied_by_cleaning_are_dropped_and_category_untouched():
    result, warnings = verify_citations(
        {
            "suggested_category": "Compliance",
            "corrective_actions": ["(RBI/2023-24/xx)", "Retest the approval flow"],
            "follow_up_actions": "Brief the team",
        },
        POLICIES,
    )
    assert result["corrective_actions"] == ["Retest the approval flow"]
    assert result["suggested_category"] == "Compliance"
    assert result["follow_up_actions"] == "Brief the team"
    assert len(warnings) == 1
