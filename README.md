# CreatorOS MVP — Vertical Slice 1.1 E2E Ready

CreatorOS is a runnable vertical slice with FastAPI, OpenAI Agents SDK, Supabase PostgreSQL/pgvector, persistent semantic memory, Creator Host and Dashboard.

## Deployment

Set these environment variables in the hosting provider; never commit `.env`:
- `OPENAI_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `CREATOROS_MODEL` (default: `gpt-5-mini`)
- `CREATOROS_MEMORY_EXTRACTOR_MODEL` (optional)

Run with:
```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Run `sql/001_creatoros.sql` in the existing CreatorOS-MVP Supabase SQL Editor before first use.

## Local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health: `/api/health`
UI: `/`

## Security
Authentication is intentionally outside this vertical slice. Do not expose the Supabase service-role key to the browser. Add Auth, rate limiting, CORS restrictions, logging and monitoring before production use.
