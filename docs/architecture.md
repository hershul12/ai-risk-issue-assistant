# Architecture

```mermaid
flowchart LR
    U[Risk Manager] --> S[Streamlit UI]
    S --> A[FastAPI Backend]
    A --> L[LLM API]
    A --> V[(FAISS Vector DB)]
    V --> D[Past Financial Risk Data]
```

## Flow
1. The user enters a financial risk or issue in the Streamlit UI.
2. The UI sends it to the FastAPI backend.
3. The backend searches FAISS for similar past financial risks.
4. The backend sends the text and similar risks to the LLM.
5. The LLM returns the category, severity, probability and mitigation.
6. The result is shown to the user.