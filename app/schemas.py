from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    memories_used: list[dict[str, Any]] = Field(default_factory=list)
    memories_saved: list[dict[str, Any]] = Field(default_factory=list)


class MemoryCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=4000)
    memory_type: str = Field(default="preference", max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryItem(BaseModel):
    id: str
    content: str
    memory_type: str
    metadata: dict[str, Any]
    similarity: float | None = None
    created_at: datetime | None = None


class MemoryExtraction(BaseModel):
    should_save: bool = Field(description="True only if the conversation contains durable creator-specific information worth remembering.")
    memories: list[str] = Field(default_factory=list, max_length=5, description="Short, atomic, reusable memories. Empty when should_save is false.")
    memory_type: str = Field(default="fact", max_length=80)


class DashboardResponse(BaseModel):
    user_id: str
    memories: list[MemoryItem]
    recent_messages: list[dict[str, Any]]
