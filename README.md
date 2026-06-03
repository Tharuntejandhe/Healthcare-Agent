# MediHealth - Healthcare AI Platform

A production-grade, multi-agent healthcare AI orchestration platform built with **FastAPI**, **LangGraph**, and **Next.js**. This system enables medical report analysis, patient data isolation, and intelligent clinical consultations using specialized AI agents.

---

## 🚀 Quick Setup Guide

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 20+** (Next.js 16 requires Node ≥ 20.9)
- **npm** or **yarn**
- A **Groq API key** (LLM/vision/speech). Postgres (Neon) for production; SQLite works for dev.
- *(Optional)* Azure Blob Storage — only if you set `STORAGE_BACKEND=azure`; defaults to local disk.

---

## 🛠️ Backend Setup (FastAPI)

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and Activate Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Includes SQLAlchemy, LangGraph, Azure Storage, and FAISS.*

4. **Configure Environment Variables:**
   - Copy the example file: `cp .env.example .env`
   - Fill in the required keys:
     - `GROQ_API_KEY`: Required for LLM orchestration.
     - `AZURE_STORAGE_CONNECTION_STRING`: Required for secure PDF storage.
     - `TAVILY_API_KEY`: Optional but recommended for web search capabilities.
     - `DATABASE_URL`: Defaults to local SQLite (`sqlite:///./sql_app.db`).
     - `SECRET_KEY`: Set a secure string for JWT authentication.

5. **Apply database migrations:**
   ```bash
   # Fresh install — creates the schema from scratch.
   alembic upgrade head

   # If you already have a legacy sql_app.db with the pre-OAuth schema,
   # stamp the baseline first so Alembic doesn't re-create the users table:
   alembic stamp 0001
   alembic upgrade head
   ```
   For dev convenience, the app also runs `Base.metadata.create_all()` on
   startup as a fallback — but Alembic is the source of truth in any
   non-toy environment.

6. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be live at `http://localhost:8000`.

---

## 🔐 Google Sign-In Setup

1. Create an **OAuth 2.0 Web Client** in [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
2. Add **Authorized JavaScript origins**: e.g. `http://localhost:3000` (dev) and your production domain.
3. Copy the **Web Client ID** into:
   - `backend/.env` → `GOOGLE_CLIENT_ID=...`
   - `frontend/.env.local` → `NEXT_PUBLIC_GOOGLE_CLIENT_ID=...`
4. Restart both servers.

The frontend uses Google Identity Services to obtain an ID token, which the
backend verifies via `google-auth`. No client secret is needed for this flow
because the ID token is verified server-side.

---

## ⚙️ Production Notes

- Set `ENVIRONMENT=production` and a strong `SECRET_KEY` (≥32 chars).
- Set `BACKEND_CORS_ORIGINS` to an explicit list of your frontend domains —
  the config validator will refuse `*` in production.
- The app emits **structured JSON logs** in production and human-readable
  text logs in development. Every log line carries a per-request ID via the
  `X-Request-ID` response header.
- Security headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy: strict-origin-when-cross-origin`, plus HSTS in production)
  are applied to every response.

---

## 💻 Frontend Setup (Next.js)

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Dependencies:**
   ```bash
   npm install
   ```

3. **Launch Development Server:**
   ```bash
   npm run dev
   ```
   Access the dashboard at `http://localhost:3000`.

---

## 📂 Project Architecture

- **`backend/`**: 
  - `app/api/`: REST endpoints for Auth, Chat, and Documents.
  - `app/services/ai/`: LangGraph agents (Senior/Junior Doctor, Nutritionist).
  - `app/services/ai/rag.py`: User-scoped FAISS vector indexing.
  - `app/services/ai/mcp_server.py`: Medical Tool Server (Drug interactions, Cardiac risk).
- **`frontend/`**: 
  - Next.js 16 (App Router) with CSS Modules.
  - Premium Dashboard with real-time AI indexing status.
- **`data/`**: Local storage for FAISS indices (user-partitioned).

---

## 🧪 Key Features & Design
- **Multi-Agent Orchestration**: Intelligent routing between general support and specialized medical agents.
- **Privacy First**: Medical reports + FAISS indices are stored per-user (local disk by default; Azure Blob optional).
- **Claymorphism UI**: Soft, tactile clay surfaces with rich micro-interactions (motion + lucide), dark mode, reduced-motion support.
- **Production-hardened**: non-blocking AI calls, timeouts + retries, rate limiting, streamed upload caps + magic-byte validation, safe error envelope, structured JSON logs.
- **Model Context Protocol (MCP)**: Local medical tools integrated directly into the LLM's reasoning loop.

---

## 🚀 Deployment
Production runs on **Vercel** (frontend) + **Render** (backend) + **Neon** (Postgres) — no Azure required.
See **[DEPLOY.md](DEPLOY.md)** for the full step-by-step guide. Local full-stack dev: `docker compose up --build`.

---

## 📝 License
Proprietary - MediHealth.
