# ReviewAIFlask

A Flask rewrite of [ReviewAI](https://github.com/civarry/ReviewAI), built to move off Streamlit and get proper control over the UI layout and multi-user support that a script-based Streamlit app can't easily give.

Like the original, it turns an uploaded document into AI-generated study questions and grades your answers against it — but this version adds Google sign-in and keeps each user's documents and embeddings isolated from everyone else's.

## What it does

1. Sign in with Google (OAuth 2.0, via `oauthlib` and `flask-login`).
2. Upload a `.txt`, `.pdf`, `.docx`, or `.csv` file. `DocumentProcessor` extracts the text (`PyPDF2` for PDFs, `python-docx` for Word, `pandas` for CSV) and splits it into chunks with configurable size and overlap.
3. Chunks are embedded with a local `sentence-transformers` model and stored in a per-user Chroma collection under `user_data/<user_id>/embeddings`, so one user's documents never leak into another's retrieval results.
4. Pick a question count and difficulty; `RAGService` builds a `RetrievalQA` chain (via LangChain) backed by a Groq-hosted LLM (`llama-3.3-70b-versatile`) and generates questions grounded in the uploaded document.
5. Answer the questions and submit — the same chain evaluates your answers against the source material and returns feedback.

## Stack

- **Flask** + **Flask-Login** for the app and session/auth management
- **Google OAuth 2.0** (`oauthlib`) for sign-in
- **LangChain** (`RetrievalQA`) tying retrieval to generation
- **ChromaDB** for per-user vector storage
- **HuggingFace `sentence-transformers`** for local embeddings
- **Groq** as the LLM backend
- **PyPDF2** / **python-docx** / **pandas** for document parsing across file types

## Setup

```
pip install -r requirements.txt
```

Requires a `.env` file with `SECRET_KEY`, `groq_api_key`, `google_client_id`, and `google_client_secret` (a Google Cloud OAuth client with the redirect URI set to `/login/callback`).

```
python app.py
```

Runs on `http://0.0.0.0:5000` by default (configurable via the `PORT` env var).
