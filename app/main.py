from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .db import Database
from .memory import MemoryService
from .schemas import ChatRequest, ChatResponse, MemoryCreate, DashboardResponse, MemoryItem
from .agent import run_creator_host


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings()
    yield


app = FastAPI(title="CreatorOS MVP", version="1.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


def services() -> tuple[Database, MemoryService]:
    db = Database()
    return db, MemoryService(db)


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health():
    settings = get_settings()
    try:
        db = Database()
        db.ping()
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        await client.models.retrieve(settings.creatoros_model)
        return {"status": "ok", "service": "CreatorOS", "version": "1.1.0", "supabase": "ok", "openai": "ok"}
    except Exception as exc:
        detail = str(exc) if settings.creatoros_debug else "Dependency health check failed"
        raise HTTPException(status_code=503, detail=detail) from exc


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    settings = get_settings()
    try:
        db, memory = services()
        conversation_id = db.get_or_create_conversation(payload.user_id, payload.conversation_id)
        memories = await memory.retrieve(payload.user_id, payload.message)
        recent = db.recent_messages(payload.user_id, limit=12)
        recent_context = "\n".join(f"{m['role']}: {m['content']}" for m in recent)
        memory_context = "\n".join(f"- {m['content']} (similaridad={m.get('similarity', 0):.2f})" for m in memories)
        db.save_message(conversation_id, "user", payload.message)
        answer = await run_creator_host(payload.message, memory_context, recent_context)
        db.save_message(conversation_id, "assistant", answer)
        try:
            saved = await memory.extract_and_save(payload.user_id, payload.message, answer)
        except Exception:
            saved = []
        return ChatResponse(conversation_id=conversation_id, answer=answer, memories_used=memories, memories_saved=saved)
    except Exception as exc:
        detail = str(exc) if settings.creatoros_debug else "CreatorOS chat request failed"
        raise HTTPException(status_code=500, detail=detail) from exc


@app.post("/api/memories", response_model=MemoryItem)
async def create_memory(payload: MemoryCreate):
    settings = get_settings()
    try:
        _, memory = services()
        result = await memory.remember(payload.user_id, payload.content, payload.memory_type, payload.metadata)
        if result is None:
            raise HTTPException(status_code=409, detail="Memory already exists")
        return MemoryItem(id=result["id"], content=result["content"], memory_type=result["memory_type"], metadata=result.get("metadata", {}), created_at=result.get("created_at"))
    except HTTPException:
        raise
    except Exception as exc:
        detail = str(exc) if settings.creatoros_debug else "Memory request failed"
        raise HTTPException(status_code=500, detail=detail) from exc


@app.get("/api/memories", response_model=list[MemoryItem])
async def memories(user_id: str):
    settings = get_settings()
    try:
        db = Database()
        return db.list_memories(user_id)
    except Exception as exc:
        detail = str(exc) if settings.creatoros_debug else "Memory request failed"
        raise HTTPException(status_code=500, detail=detail) from exc


@app.get("/api/dashboard", response_model=DashboardResponse)
async def dashboard(user_id: str):
    settings = get_settings()
    try:
        db = Database()
        return DashboardResponse(user_id=user_id, memories=db.list_memories(user_id), recent_messages=db.recent_messages(user_id))
    except Exception as exc:
        detail = str(exc) if settings.creatoros_debug else "Dashboard request failed"
        raise HTTPException(status_code=500, detail=detail) from exc
