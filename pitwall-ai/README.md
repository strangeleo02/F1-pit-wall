# PitWall AI

An interactive F1 telemetry and radio transcript RAG application.

This application combines numerical F1 telemetry via the `FastF1` Python library with unstructured text retrieval (team radio transcripts) using Qdrant Cloud and Groq LLM inference.

## Directory Structure

- `backend/`: FastAPI application handling logic, data fetching (FastF1), embeddings generation, vector search (Qdrant), and LLM inference (Groq).

## Quickstart

1. **Clone the repository**
2. **Environment Variables**
   - Copy `.env.example` to `.env` and fill in your API keys (Groq, Qdrant).
3. **Backend**
   - Navigate to `backend/` and install requirements: `pip install -r requirements.txt`
   - Run the FastAPI server: `uvicorn app.main:app --reload`

## Docker

The backend has a `Dockerfile` if you prefer containerized deployment.
