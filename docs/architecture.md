# Architecture

## System Overview

```mermaid
flowchart TB
    U["Risk Manager"] --> UI

    subgraph UI["Frontend - React + Vite"]
        FORM["Risk Input Form"]
        RESULT["Analysis Result Cards"]
        SIMILAR["Similar Past Risks Panel"]
    end

    UI -->|"HTTP JSON"| API

    subgraph API["Backend - FastAPI"]
        MW["Middleware: CORS, Logging, Error Handling"]
        R1["GET /health"]
        R2["POST /analyze"]
        R3["POST /similar"]
        MW --> R1
        MW --> R2
        MW --> R3
    end

    R2 --> VS["Vector Service"]
    R3 --> VS
    R2 --> LLMS["LLM Service"]

    subgraph RAG["Retrieval Layer"]
        CSV["sample_risks.csv"] --> TFIDF["TF-IDF Vectorizer"]
        TFIDF --> FAISS[("FAISS Index")]
    end

    VS --> FAISS
    LLMS -->|"Prompt + similar risks"| GROQ["Groq API - GPT-OSS"]
    GROQ -->|"JSON: category, severity, probability, mitigation"| LLMS

    subgraph DEVOPS["Deployment - planned for Day 34"]
        GH["GitHub Repo"] --> CICD["CI/CD Pipeline"]
        CICD --> DOCKER["Docker Image"]
        DOCKER --> AZURE["Azure Hosting"]
    end
```

## Components

| Layer | Component | Responsibility |
|-------|-----------|----------------|
| Frontend | React + Vite | Input form, result cards, similar risks panel |
| Backend | FastAPI | REST API, validation, CORS, error handling |
| LLM Service | Groq API (GPT-OSS) | Classifies the risk and suggests mitigation |
| Vector Service | TF-IDF + FAISS | Finds similar past financial risks |
| Data | sample_risks.csv | Knowledge base of past risks and mitigations |
| DevOps | GitHub, Docker, Azure | Version control, containers, hosting |

## Request Flow (POST /analyze)
1. The user types a financial risk or issue in the React form.
2. React sends the text to the FastAPI backend as JSON.
3. The Vector Service converts the text to a TF-IDF vector.
4. FAISS returns the 3 most similar past risks.
5. The LLM Service sends the text and the similar risks to the Groq model.
6. The model returns the type, category, severity, probability and mitigation.
7. The backend returns the result with the similar risks.
8. React shows the result cards and the similar risks panel.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | /health | Check that the server is running |
| POST | /analyze | Classify, rate and suggest mitigation |
| POST | /similar | Return similar past risks only |