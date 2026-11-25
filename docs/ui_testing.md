# UI Testing and Feedback

## Test checklist
| Check | Result |
|-------|--------|
| Dashboard loads with summary, matrix and register | Pass |
| Filters (status, priority, category, owner, overdue, search) | Pass |
| Risk matrix cell filters the register | Pass |
| Create record with calculated score | Pass |
| AI draft shown as a suggestion and used only after review | Pass |
| Role rules: only Project Manager can create | Pass |
| Review workflow: submit, send back, approve and close | Pass |
| Error state when the backend is stopped | Pass |
| Backend logs every request | Pass |
| Import from text: AI extracts risks from an email, ignores non-risk lines | Pass |
| Draft with AI: structured output (cause, impact, warning indicators, preventive, corrective, contingency) with similar past risks | Pass |
| Bank policy upload and policy page cited in the AI draft | Pass |
| Out-of-scope text shows "No AI draft" (fallback) | Pass |
| Live website on Azure App Service works end to end (dashboard, AI, policy upload) | Pass |

## Feedback log
| Feedback | Change made |
|----------|-------------|
| Mentor: problem statement unclear - is it banking, which risks, how is AI relevant to banking | Rescoped to banking technology programmes with 8 risk types, banking rules in AI prompts, 48 banking example risks, and bank policy upload |
| Mentor: shared a list of suggested AI capabilities (structured risk output, duplicate detection, early warnings, stakeholder reports) | Added structured AI output (cause, potential impact, warning indicators, preventive, corrective and contingency actions); the rest is planned as next steps |

## Peer review
| Reviewer | Feedback | Change made / response |
|----------|----------|------------------------|
| Piyush | The problem statement was not clear at first; after the update it is clear, and the app is good and easy to follow | Problem statement rewritten for banking technology programmes, with a clear scope and 8 risk types (same change as the mentor feedback) |