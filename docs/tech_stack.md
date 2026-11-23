# Tech Stack

| Layer | Tool |
|-------|------|
| Frontend | React (Vite) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL with SQLAlchemy (SQLite for quick local runs) |
| Database tool | pgAdmin |
| LLM | Azure OpenAI |
| Embeddings | TF-IDF (scikit-learn) |
| Vector search | FAISS (similar past risks and bank policy passages) |
| PDF reading | pypdf |
| Cloud | Microsoft Azure |
| Version Control | Git and GitHub |
| Containerization | Docker |
| IDE | VS Code |

## Deviations from the Trainer's Brief

| Brief | Used | Reason |
|-------|------|--------|
| Streamlit | React (Vite) | The workflow needs role-based controls, a clickable risk matrix, a side panel for review, and a separate REST API. React gives full control of this interface, and the FastAPI backend works with any frontend. |
| Neural embeddings | TF-IDF vectors with FAISS | Needs no extra API key, runs instantly on a small knowledge base and is easy to explain. FAISS performs the vector search. Upgrade path: replace TF-IDF with Azure OpenAI embeddings and keep FAISS. |