# Architecture

```mermaid
flowchart TB
    U["Users: Project Manager, Risk Owner, Programme Lead"] --> UI

    subgraph UI["Frontend - React + Vite"]
        FORM["Risk and Issue Form"]
        DASH["Dashboard: open, overdue, high priority"]
        FILT["Filters and Status Indicators"]
        REV["Human Review Panel"]
    end

    UI -->|"REST JSON"| API

    subgraph API["Backend - FastAPI"]
        AUTH["Role Check (X-Role header)"]
        CRUD["CRUD Endpoints"]
        SCORE["Scoring Engine: probability x impact"]
        SUGG["AI Suggestion Endpoint"]
        AUDIT["Audit Log Writer"]
        AUTH --> CRUD
        AUTH --> SUGG
        CRUD --> SCORE
        CRUD --> AUDIT
    end

    CRUD --> DB[("Relational Database: items, audit_log")]
    AUDIT --> DB
    SUGG --> LLM["LLM Service"]
    LLM -->|"Prompt"| GROQ["Groq API - GPT-OSS"]
    GROQ -->|"Draft description and mitigation"| SUGG
    SUGG -.->|"optional"| SIM["Similar Items: TF-IDF and FAISS"]

    subgraph DEVOPS["Deployment - Day 34"]
        GH["GitHub Repo"] --> CICD["CI/CD Pipeline"]
        CICD --> DOCKER["Docker Image"]
        DOCKER --> AZURE["Azure Hosting"]
    end
```

## Key Design Rules
- Scoring is deterministic: Probability x Impact, with fixed priority bands.
- The LLM only drafts text. Its output is a suggestion and a human must accept it.
- Status changes and approvals are made by users with the right role.
- Every change is written to the audit log.