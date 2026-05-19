# SilentChair

AI workforce platform — hire agents to build and run your business.

## Structure

```
SilentChair/
├── frontend/        # Next.js 15 + TypeScript + shadcn/ui
├── backend/         # FastAPI + LangGraph + Anthropic
└── supabase/        # Schema migrations
```

## Quick Start

### 1. Supabase
- Create a project at supabase.com
- Run `supabase/migrations/001_initial_schema.sql` in the SQL editor
- Copy your project URL and anon key

### 2. Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env        # fill in your keys
python run.py
```

### 3. Frontend
```bash
cd frontend
copy .env.local.example .env.local   # fill in your Supabase keys
npm install
npm run dev
```

Open http://localhost:3000

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, shadcn/ui, Tailwind |
| Backend | FastAPI, LangGraph, Anthropic Claude |
| Database | Supabase (PostgreSQL + pgvector + Auth) |
| Queue | Celery + Redis (Phase 3) |
| Deploy | Vercel (frontend) + Railway (backend) |
