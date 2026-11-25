# Learnings

What I learned building RiskPilot, an AI-assisted risk and issue register for banking
technology programmes.

## What went well

- **Fixed scoring plus AI help gave a clear, trustworthy design.** The AI suggests, people
  decide, and the formula (Probability x Impact) sets the priority. Nobody has to wonder
  whether the AI changed a score.
- **RAG made the AI answers relevant and checkable.** Giving the AI similar past banking
  risks and the bank's own policies meant its drafts fit the domain, and because it cites the
  policy and page, a reviewer can check every claim.
- **One container made deployment simple.** FastAPI serves the React app and the API, so
  there is one app to build, one image to deploy and one URL to share.
- **CI/CD caught problems early.** Lint, tests and a Docker smoke test run before anything is
  deployed, and every push to `master` deploys automatically.

## Challenges and what I learned

1. **A clear problem statement matters more than features.** My mentor said the scope was not
   clear: is it for banking, and which risks? I had been adding features before answering
   that.
   *Learning:* define who it is for and what is in and out of scope before adding features.

2. **AI must be tested, not trusted.** The evaluation found the AI inventing a policy
   citation and giving full answers to text that had nothing to do with banking risks. I
   added a citation guard and a scope check, and the out-of-scope fallback went from 0/3
   to 3/3.
   *Learning:* always measure AI output with test cases and add checks around it.

3. **Prompt injection is real.** After I made the prompt stricter, the AI once replied
   "APPROVED" because the text told it to.
   *Learning:* tell the AI that user text is data, not instructions, and test for it.

4. **Small configuration mistakes cause big errors.** An "@" in the database password broke
   the connection address and gave a 503. An old image kept running and showed "Not Found".
   A wrong port stops the app answering at all.
   *Learning:* read the logs first; they show the exact cause.

5. **Keep secrets out of code.** Keys and passwords live in `.env` and Azure settings, never
   in GitHub, and I keep the live URL private because there is no login.
   *Learning:* treat secrets and access as part of the design, not an afterthought.

## What I would do differently

- Plan the database and deployment early, not at the end.
- Start the AI evaluation earlier, so problems show up while there is time to fix them.
- Add Microsoft sign-in early, since roles matter in banking.
- Use meaning-based embeddings instead of TF-IDF for better retrieval.

## Next steps

- Microsoft sign-in (Microsoft Entra ID) instead of the role selector
- Azure OpenAI embeddings for retrieval, keeping FAISS
- Duplicate risk detection when a new record is created
- AI risk summary and early warnings for the programme lead
- Database migrations with Alembic

## My own notes

The hardest part for me was making the AI reliable. The evaluation showed it could invent
a policy citation and answer unrelated questions. Fixing that with a citation guard and a
scope check taught me that building with AI means testing it, not just calling it.
