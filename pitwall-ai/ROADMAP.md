# 🏎️ PitWall AI — Technical & Product Roadmap

This itemized roadmap outlines the development plan for **PitWall AI**, progressing from core architecture refactoring to multi-modal data ingestion, advanced RAG routing, interactive UI components, and zero-cost cloud deployment.

---

## 📌 Phase 1: Core Backend Refactoring & Reliability (Technical Debt & Foundation)

- [x] **1.1 Non-Blocking Async Architecture & Threadpooling**
  - Offload heavy `FastF1` data loading and `SentenceTransformer` vector encoding calls to worker threadpools using `fastapi.concurrency.run_in_threadpool`.
  - Transition Groq and Qdrant database clients to `AsyncGroq` and `AsyncQdrantClient` to ensure the FastAPI event loop remains non-blocking under concurrent requests.

- [x] **1.2 FastAPI Dependency Injection & Lifespan Management**
  - Replace module-level global client singletons (`client = ...`, `qdrant_client = ...`) with FastAPI `Depends()` dependency injection.
  - Implement `@asynccontextmanager` lifespan handlers in `app/main.py` for client initialization and shutdown.

- [x] **1.3 Strict Pydantic Schema Validation & CORS Hardening**
  - Add regex constraints and validators in `StrategyQueryRequest` for 3-letter driver codes (`^[A-Z]{3}$`), session types (`R`, `Q`, `FP1`, `FP2`, `FP3`), and valid F1 year ranges.
  - Restrict CORS origins via `pydantic-settings` to replace wildcard `allow_origins=["*"]` in production.

- [x] **1.4 Standardized Domain Exceptions & Response Contracts**
  - Replace dictionary returns containing `"error"` keys with custom Python domain exceptions (`TelemetryNotFoundError`, `VectorDBUnavailableError`).
  - Implement FastAPI exception handlers to return standard, structured HTTP response codes (`400`, `404`, `503`).

- [x] **1.5 Expanded Automated Test Suite**
  - Add comprehensive unit and integration tests for async service layers, mock error paths, and response contracts in `backend/tests/`.

---

## 📌 Phase 2: Multi-Modal Data Ingestion & Indexing Pipeline

- [x] **2.1 OpenF1 API Radio Transcript Ingestion Engine**
  - Build an automated ingestion script to fetch driver radio transcripts and race control messages from the OpenF1 API.
  - Normalize timestamps, driver codes, session types, and lap references.

- [x] **2.2 Qdrant Vector Store Payload Schema & Indexing**
  - Define Qdrant collection schemas with Cosine distance metric for `all-MiniLM-L6-v2` embeddings.
  - Implement batch embedding generation with structured payload fields (`driver`, `session`, `lap_start`, `lap_end`, `team`, `transcript_text`).

- [x] **2.3 Telemetry Time-Series Cache Optimization**
  - Implement pre-warming disk caching for `FastF1` telemetry sessions to maintain < 15ms telemetry retrieval latency.
  - Extract detailed time-series telemetry streams (speed, throttle percentage, braking zones, gear selection).

---

## 📌 Phase 3: Query Intent Router & Multi-Modal Context Synthesizer

- [x] **3.1 Intelligent Query Intent Router**
  - Develop a query classification module to detect user intent and dynamically determine retrieval requirements (telemetry-only, radio transcript search, or full multi-modal RAG).

- [x] **3.2 Multi-Modal Context Synthesizer Engine**
  - Build time-delta correlation logic to match lap time drops/spikes with corresponding driver complaints or pit-wall audio timestamps.
  - Format telemetry statistical summaries (lap delta, max speed, average throttle) and retrieved radio quotes into a unified prompt schema.

- [x] **3.3 Upgrade LLM Engine to Groq (Llama 3.3 70B Versatile)**
  - Upgrade the Groq model endpoint to `llama-3.3-70b-versatile` for higher reasoning quality and faster inference.
  - Implement Server-Sent Events (SSE) streaming endpoint (`/api/v1/strategy/stream`) for real-time response generation.

---

## 📌 Phase 4: Modern Next.js Interactive Dashboard

- [ ] **4.1 Next.js Frontend Application**
  - Build a modern, sleek, dark-themed Next.js App Router web application tailored for F1 pit-wall strategy analysis.
  - Implement interactive selectors for year, Grand Prix location, session type, driver code, and natural language strategy prompt input.
  - Integrate real-time Server-Sent Events (SSE) streaming (`/api/v1/strategy/stream`) for token-by-token LLM strategy insights.

- [ ] **4.2 Interactive Telemetry Charts (Recharts / Chart.js)**
  - Build interactive telemetry overlay charts displaying speed traces, throttle profiles, braking points, and lap time deltas.
  - Highlight specific lap numbers and telemetry anomalies referenced in the AI strategy breakdown.

- [ ] **4.3 Radio Transcript Feed & Audio Player UI**
  - Render expandable, filterable team radio transcript cards and FIA race control messages alongside AI insights.
  - Include built-in audio playback controls for driver team radio MP3 URLs.

---

## 📌 Phase 5: CI/CD, Containerization & Cloud Deployment

- [ ] **5.1 Multi-Stage Dockerfile Optimization**
  - Optimize Dockerfiles for both backend (FastAPI) and frontend (Next.js) using multi-stage builds to minimize image size and improve startup latency.

- [ ] **5.2 GitHub Actions CI/CD Pipeline**
  - Configure automated linting (`ruff`/`ESLint`), type checking (`mypy`/`TypeScript`), and test execution (`pytest`) on pull requests.

- [ ] **5.3 $0 Infrastructure Deployment**
  - Host the Next.js frontend on Vercel and backend API on free container hosting.
  - Connect with Qdrant Cloud (Free Tier) and Groq Cloud API (`llama-3.3-70b-versatile`).
