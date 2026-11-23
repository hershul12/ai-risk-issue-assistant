# Problem Statement

Banks run large technology change programmes such as core banking upgrades,
payment systems (UPI, NEFT, RTGS), digital lending, KYC and AML remediation,
mobile banking and regulatory reporting. Delivery risks and issues in these
programmes are recorded inconsistently across emails, spreadsheets, meeting
notes and task tools. As a result, ownership is unclear, severity is judged
differently by different people, follow-up is missed, and there is no
reliable record of decisions. In banking, this can lead to missed regulatory
deadlines, customer-impacting outages, audit findings and cost overruns.

# Scope

RiskPilot manages project delivery risks and issues in banking technology
programmes. It does not manage the bank's financial risks such as credit,
market or liquidity risk, which need specialised risk systems.

- Risk: something that might go wrong in the future
- Issue: a problem that has already happened

| Category | Banking programme examples |
|----------|----------------------------|
| Compliance | New RBI circular not assessed; KYC norms changed mid-project |
| Security | Penetration test finds vulnerabilities; customer data exposed in testing |
| Technical | Core banking data migration errors; payment switch failure |
| Vendor | Payment gateway or SMS-OTP provider outage; vendor delays API documents |
| Schedule | Regulatory go-live deadline at risk; UAT sign-off delayed |
| Budget | Cloud or licence costs above budget; change requests not funded |
| Resource | Key developers resign; no AML domain expert on the team |
| Scope | New features keep being added; loan journey design not approved |

# Goal

Create a governed risk and issue register for banking programmes that
captures records consistently, scores them with a fixed formula, extracts
risks from emails and meeting notes, drafts clear descriptions and mitigation
plans for owners to review, and requires approval before a record is closed.

# Target Users

- Project Manager: records and manages risks and issues
- Risk/Issue Owner: works on the mitigation and submits for review
- Programme Lead: reviews, then approves and closes or sends back

# Domain

Financial Risk Management (banking technology programmes)

# Project Objectives

- Capture risks and issues consistently in one register
- Score every record with probability x impact (Low, Medium, High, Critical)
- Extract risks and issues from emails and meeting notes using AI
- Draft clear descriptions, mitigation plans and follow-up actions using AI
- Ground AI suggestions in similar past risks (RAG)
- Enforce role-based review and approval before closure
- Keep a full audit trail of every change
- Show open, overdue, high-priority and awaiting-review items

# How AI Stays Relevant to Banking

- The AI is instructed to act as a risk analyst in a bank programme office
- Before drafting, the system retrieves similar past risks and their
  mitigations, and gives them to the AI as examples (RAG)
- If no similar risk exists, the AI drafts from the description and its
  general knowledge, and the reviewer checks it
- The AI never decides the score, priority or status, and nothing is saved
  until a person reviews and accepts it

# Project Type

AI-assisted summarizer and recommender: it summarises rough text into clear
risk statements, extracts risks and issues from emails and meeting notes,
and recommends a category, mitigation, follow-up actions and similar past
risks.