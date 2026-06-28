<p align="center">
  <h1 align="center">📰 Autonomous News Intelligence Platform</h1>
  <p align="center">
    <strong>Agentic AI × Generative RAG × Deep Learning Anomaly Detection</strong>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Next.js_15-000000?logo=next.js&logoColor=white" alt="Next.js 15">
    <img src="https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B?logo=langchain&logoColor=white" alt="LangGraph">
    <img src="https://img.shields.io/badge/Qdrant-Vector%20RAG-dc143c?logo=qdrant&logoColor=white" alt="Qdrant">
    <img src="https://img.shields.io/badge/PostgreSQL-ORM Layer-316192?logo=postgresql&logoColor=white" alt="PostgreSQL">
    <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white" alt="Docker">
    <img src="https://img.shields.io/badge/BERTopic-Deep%20NLP-4285f4?logo=google&logoColor=white" alt="BERTopic">
    <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  </p>
</p>

---

## 🌟 Overview

The **Autonomous News Intelligence Platform** is an enterprise-grade AI system that continuously ingests massive news corpuses (200,000+ articles), discovers emerging real-world events using unsupervised deep learning, synthesizes executive intelligence briefings via a **LangGraph multi-agent state machine**, and answers user queries through **Generative RAG** grounded in vector search.

Originally developed as a classical NLP anomaly detector (*Dynamic Trend & Event Detector*), this platform has been engineered into a full production AI architecture featuring swappable ML backends, multi-collection vector indexing, self-reflective agent loops, human-in-the-loop review gates, and a sleek **Next.js 15 dark glassmorphism dashboard**.

---

## 💡 Key Architectural Pillars

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               AUTONOMOUS AI PLATFORM                                   │
│                                                                                        │
│  ┌─────────────────────────┐   ┌─────────────────────────┐   ┌──────────────────────┐  │
│  │     1. SIGNAL ENGINE    │   │    2. AGENTIC STATE     │   │   3. GENERATIVE RAG  │  │
│  │                         │   │                         │   │                      │  │
│  │  • Sentence-BERT        │──▶│  • LangGraph Workflow   │──▶│  • Qdrant Vector DB  │  │
│  │  • UMAP + HDBSCAN       │   │  • 8 Specialized Roles  │   │  • 5 Index Collections│  │
│  │  • Semantic Velocity    │   │  • Self-Reflection Gate │   │  • Cited Inline RAG  │  │
│  └─────────────────────────┘   └─────────────────────────┘   └──────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1. Core ML Anomaly Detection (`services/topic_discovery/`)
* **Deep Learning Topic Modeling**: Employs Sentence-BERT embeddings, UMAP dimensionality reduction, and HDBSCAN density clustering. Outperforms baseline LDA models by improving topic coherence ($C_v$) by **39.4%** ($0.4981$ vs $0.3573$).
* **Automatic Fallback Guard**: Dynamically drops back to keyword clustering on small corpora ($N < 20$) to prevent UMAP crashes during streaming ingestion.
* **Semantic Velocity Tracking**: Calculates rate-of-change across time windows to separate breaking real-world events from slowly drifting viral topics.

### 2. LangGraph Multi-Agent State Machine (`services/agents/`)
Instead of single-shot prompt calls, candidate events are passed into a deterministic, self-reflective 10-node execution graph:
1. **Research Agent**: Pulls contextual evidence across RAG collections.
2. **Fact Verification Agent**: Cross-references claims against reliability scores.
3. **Domain Impact Agents**: Fan-out execution evaluating **Business**, **Economic**, and **Risk** dimensions.
4. **Executive Summary Agent**: Synthesizes structured markdown briefings.
5. **Reflection Agent**: Self-critiques outputs for hallucinations. If confidence falls below 65%, execution pauses and routes to a **Human-in-the-Loop Analyst Gate**.

### 3. Generative RAG Vector Layer (`services/retrieval/`)
Backed by **Qdrant**, the platform indexes data across 5 distinct collections:
* `article_chunks`: Semantic indexing of raw incoming news texts.
* `event_summaries`: Historical analog event matching.
* `reports`: Published AI executive briefs.
* `agent_memory` & `analyst_corrections`: Episodic reflection storage learning from human analyst overrides.

---

## 📊 Performance Benchmarks

| Model / Approach | Coherence ($C_v$) | Temporal Tracking | RAG Grounding | Multi-Agent Synthesis |
|---|:---:|:---:|:---:|:---:|
| LDA Baseline | 0.3573 | ❌ | ❌ | ❌ |
| Pure BERTopic | 0.4781 | ❌ | ❌ | ❌ |
| **Autonomous Platform** | **0.4981** | ✅ | ✅ | ✅ |

---

## 🚀 Quick Start & Running Locally

### Option 1: Full Docker Compose Stack (Recommended)
Launch the complete containerized platform (Nginx, Next.js UI, FastAPI Backend, Celery Workers, PostgreSQL, Redis, and Qdrant):

```bash
# Clone repository
git clone https://github.com/shahfathalkoul/Dynamic-Event-Detector.git
cd Dynamic-Event-Detector

# Copy environment variables
cp .env.example .env

# Launch all 8 enterprise containers
docker-compose up -d --build
```
* **Interactive Web Dashboard**: [http://localhost:3000](http://localhost:3000)
* **FastAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### Option 2: Local Development & Testing

```bash
# 1. Create Python environment and install backend dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Run the full backend test suite (28/28 tests passing)
python -m unittest discover -s tests -v

# 3. Start Next.js Frontend locally
cd apps/web
npm install
npm run dev
```

---

## 🛠️ Enterprise Tech Stack

| Layer | Technologies | Purpose |
|---|---|---|
| **Frontend UI** | Next.js 15, TypeScript, Tailwind CSS v4, Framer Motion | 12-page dark glassmorphism dashboard |
| **API Gateway** | FastAPI, Pydantic v2, Uvicorn | Asynchronous REST and streaming ingestion |
| **Agent Orchestration** | LangGraph, LangChain, OpenAI / Anthropic APIs | Stateful multi-agent reflection workflows |
| **Vector Database** | Qdrant, Sentence-Transformers | Multi-collection RAG retrieval |
| **Relational Database** | PostgreSQL, SQLAlchemy ORM, Alembic | Durable entity, memory, and audit logging |
| **Async Tasks** | Celery, Redis | Background anomaly detection and batch indexing |
| **DevOps & Observability** | Docker Compose, Nginx, OpenTelemetry, GitHub Actions | Production containerization & CI/CD pipeline |

---

## 📂 Project Architecture

```
Dynamic-Event-Detector/
├── apps/
│   ├── web/                         # Next.js 15 Enterprise Dashboard (12 pages)
│   └── api/                         # FastAPI application factory & routers
├── packages/
│   ├── common/                      # Central PlatformSettings & OpenTelemetry tracing
│   └── schemas/                     # Shared Pydantic domain records
├── services/
│   ├── agents/                      # LangGraph state machine & LLM gateway
│   ├── retrieval/                   # Qdrant multi-collection RAG retriever
│   ├── storage/                     # SQLAlchemy ORM models & PostgresRepository
│   ├── topic_discovery/             # Swappable BERTopic & Keyword NLP engines
│   └── memory/                      # Long-term agent memory store
├── infra/
│   ├── docker/                      # Production Dockerfiles (API, Worker, Web)
│   └── nginx/                       # Reverse proxy configuration
├── alembic/                         # Database schema migrations
├── tests/                           # Comprehensive automated unit & regression suite
├── docker-compose.yml               # 8-service enterprise container orchestration
└── .github/workflows/ci.yml         # Continuous integration pipeline
```

---

## 📄 License & Author

**Author:** Shah Fathal Koul  
**License:** Licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
