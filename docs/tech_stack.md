# Tech Stack

| Layer | Tool |
|-------|------|
| Frontend | React (Vite) |
| Backend | FastAPI (Python) |
| Database | SQLite with SQLAlchemy |
| LLM | Groq API (OpenAI GPT-OSS 20B) |
| Embeddings | TF-IDF (scikit-learn) |
| Vector Database | FAISS (optional, similar items) |
| Cloud | Microsoft Azure |
| Version Control | Git and GitHub |
| Containerization | Docker |
| IDE | VS Code |

## Deviations from the Trainer's Brief

| Brief | Used | Reason |
|-------|------|--------|
| Streamlit | React (Vite) | The workflow needs role-based controls, a clickable risk matrix, a side panel for review, and a separate REST API. React gives full control of this interface, and the FastAPI backend works with any frontend. |
| OpenAI API | Groq API through the official OpenAI Python SDK | Same SDK and same API format; only the address, key and model name differ. Groq gives fast, free access to OpenAI's open-weight GPT-OSS model. Switching to OpenAI or Azure OpenAI is a configuration change. |
| Neural embeddings | TF-IDF vectors with FAISS | Needs no extra API key, runs instantly on a small knowledge base and is easy to explain. FAISS performs the vector search. Upgrade path: replace TF-IDF with a sentence-embedding model and keep FAISS. |