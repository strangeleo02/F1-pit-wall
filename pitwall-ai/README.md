# 🏎️ PitWall AI — Multi-Modal F1 Race Strategy RAG System

**PitWall AI** is a high-performance, multi-modal Retrieval-Augmented Generation (RAG) platform that correlates real-time Formula 1 lap telemetry, speed traces, and braking metrics with driver team radio transmissions and FIA race control messages.

Powered by **FastAPI**, **Qdrant Vector Database**, **FastF1**, **SentenceTransformers**, and **Groq Cloud (Llama 3.3 70B Versatile)**.

---

## 🌟 Key Features

- **🏎️ Dynamic Multi-Modal RAG Engine**: Correlates lap-by-lap time deltas and telemetry anomalies with driver complaints and race control messages.
- **⚡ Intent Classification Router**: Automatically classifies user queries into `TELEMETRY_ONLY`, `RADIO_ONLY`, or `FULL_RAG` to optimize response latency and token usage.
- **📡 Multi-Collection Qdrant Vector Search**: Dual vector collections (`radio_transcripts` and `race_telemetry`) with `Cosine` similarity and indexed payload metadata (`driver`, `session`, `year`, `grand_prix`, `session_key`).
- **🌊 SSE Real-Time Streaming**: Server-Sent Events (`/api/v1/strategy/stream`) for token-by-token LLM strategy insights.
- **🚀 High-Speed Ingestion & Auto-Resumption**: Multi-season bulk ingestion scripts with dynamic session discovery and auto-skipping of indexed points.
- **⚡ In-Memory & Disk Telemetry Cache**: Sub-millisecond (<1ms) repeat telemetry query performance via multi-tier caching.

---

## 📁 Repository Structure

```
pitwall-ai/
├── backend/
│   ├── app/
│   │   ├── config.py              # Configuration & env management
│   │   ├── main.py                # FastAPI app initialization & lifespan
│   │   ├── dependencies.py        # Dependency injection (Qdrant, Groq)
│   │   ├── schemas.py             # Pydantic request/response contracts
│   │   ├── exceptions.py          # Custom domain exception handlers
│   │   ├── ingestion/             # Multi-modal radio transcript pipeline
│   │   ├── routers/               # API endpoints (/api/v1/strategy)
│   │   └── services/              # Vector DB, OpenF1, FastF1, Groq LLM services
│   ├── scripts/                   # Bulk population & indexing scripts
│   ├── tests/                     # Pytest suite (30+ unit & integration tests)
│   ├── Dockerfile                 # Multi-stage Docker build file
│   └── requirements.txt           # Python dependencies
├── .github/workflows/ci.yml       # GitHub Actions CI/CD workflow
├── docker-compose.yml             # Docker Compose configuration
├── run.py                         # Root execution entrypoint
├── ROADMAP.md                     # Project roadmap & progress tracker
├── .env.example                   # Environment configuration template
└── README.md                      # Documentation
```

---

## ⚡ Quickstart Guide

### 1. Environment Setup
Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

```env
GROQ_API_KEY=gsk_your_groq_api_key
QDRANT_URL=https://your-qdrant-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the Development Server

From the project root:

```bash
python run.py
```

The API will be live at `http://localhost:8000`. Access interactive Swagger docs at `http://localhost:8000/docs`.

---

## 📦 Data Ingestion & Qdrant Population

Populate historical F1 radio transcripts and telemetry data into Qdrant Cloud:

```bash
cd backend

# Bulk ingest & index radio transcripts and race control messages (2016-2026)
python scripts/populate_qdrant.py

# Bulk index telemetry summary vectors into 'race_telemetry' collection
python scripts/populate_qdrant_telemetry.py

# Pre-cache FastF1 timing streams onto disk
python scripts/populate_fastf1_cache.py
```

---

## 🧪 Running Automated Tests

Run the full pytest suite (30+ unit and integration tests):

```bash
cd backend
python -m pytest tests/ --verbosity=2
```

---

## 🐳 Docker Deployment

Run PitWall AI in containerized production mode using Docker Compose:

```bash
docker-compose up --build
```
