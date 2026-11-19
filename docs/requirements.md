# Requirements

## User Roles

| Role | Permissions |
|------|-------------|
| Project Manager | Create, edit and close records; view dashboard |
| Risk/Issue Owner | Update own records, add review notes, request closure |
| Programme Lead | Review records, approve closure, view dashboard |

## MVP Scope

- Define risk/issue fields and a sample register
- Create, read and update APIs
- Deterministic scoring based on agreed scales
- LLM drafts for description and mitigation, marked as suggestions
- Dashboard with filters and status indicators
- Approval and status changes stay under human control

## Out of Scope for First Release

- Automatic schedule changes
- External escalation or task creation
- Complex portfolio integration

## Record Fields

| Field | Mandatory | Notes |
|-------|-----------|-------|
| Title | Yes | Short summary |
| Description | Yes | Standardised text |
| Type | Yes | Risk or Issue |
| Category | Yes | Schedule, Budget, Scope, Resource, Technical, Vendor, Compliance, Security |
| Probability | Yes | 1 to 5 |
| Impact | Yes | 1 to 5 |
| Score | Auto | Probability x Impact |
| Priority | Auto | Low, Medium, High, Critical |
| Owner | Yes | Person responsible |
| Status | Yes | Open, In Progress, Pending Review, Closed |
| Due Date | Yes | Target date |
| Mitigation | No | Draft suggested by AI, edited by owner |
| Review Notes | No | Added by reviewer |

## Scoring Rules (assumptions, to be confirmed with mentor)

- Score = Probability x Impact (1 to 25)
- Low: 1-5, Medium: 6-12, High: 13-19, Critical: 20-25
- Overdue: due date has passed and status is not Closed
- Critical: score of 20 or more

## User Stories

1. As a project manager, I want to log a risk or issue with standard fields so that records are consistent.
2. As a project manager, I want the system to calculate the score and priority so that prioritisation is objective.
3. As an owner, I want an AI-drafted description and mitigation so that I can review and edit it quickly.
4. As an owner, I want to update the status and add review notes so that follow-up is tracked.
5. As a programme lead, I want to see open, overdue and high-priority items so that I know where to focus.
6. As a programme lead, I want every status change recorded in an audit log so that decisions can be traced.

## Acceptance Criteria

- A record cannot be saved without the mandatory fields.
- The score and priority are calculated by fixed rules, not by the AI.
- AI output is shown as a suggestion and is saved only after a human accepts it.
- Only allowed roles can change status or close a record.
- Every create, update and status change is stored in the audit log.
- The dashboard can filter by status, priority, owner and overdue.