# PitWall AI

An interactive F1 telemetry and radio transcript RAG application.

This application combines numerical F1 telemetry via the `FastF1` Python library with unstructured text retrieval (team radio transcripts) using Qdrant Cloud and Groq LLM inference.

## Directory Structure

- `backend/`: FastAPI application handling logic, data fetching (FastF1), embeddings generation, vector search (Qdrant), and LLM inference (Groq).

## Quickstart

1. **Install requirements**
   - `pip install -r backend/requirements.txt`
2. **Environment Variables**
   - Copy `.env.example` to `.env` and fill in your API keys (Groq, Qdrant).
3. **Run the Application**
   - Run directly from the root directory:
     ```bash
     python run.py
     ```
   - Or navigate to `backend/` and run:
     ```bash
     uvicorn app.main:app --reload
     ```

## Docker

The backend has a `Dockerfile` if you prefer containerized deployment.
