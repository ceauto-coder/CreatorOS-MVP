from hashlib import sha256
from typing import Any
from supabase import Client, create_client
from .config import get_settings


class Database:
    def __init__(self) -> None:
        settings = get_settings()
        self.client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    def ping(self) -> bool:
        self.client.table("creatoros_conversations").select("id").limit(1).execute()
        return True

    def get_or_create_conversation(self, external_user_id: str, conversation_id: str | None = None) -> str:
        if conversation_id:
            result = (
                self.client.table("creatoros_conversations")
                .select("id")
                .eq("id", conversation_id)
                .eq("external_user_id", external_user_id)
                .limit(1)
                .execute()
            )
            if result.data:
                return result.data[0]["id"]
        result = self.client.table("creatoros_conversations").insert({"external_user_id": external_user_id, "title": "CreatorOS Session"}).execute()
        return result.data[0]["id"]

    def save_message(self, conversation_id: str, role: str, content: str) -> None:
        self.client.table("creatoros_messages").insert({"conversation_id": conversation_id, "role": role, "content": content}).execute()
        self.client.table("creatoros_conversations").update({"title": "CreatorOS Session"}).eq("id", conversation_id).execute()

    def recent_messages(self, external_user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        conv = (
            self.client.table("creatoros_conversations")
            .select("id")
            .eq("external_user_id", external_user_id)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        if not conv.data:
            return []
        rows = (
            self.client.table("creatoros_messages")
            .select("id,role,content,created_at")
            .eq("conversation_id", conv.data[0]["id"])
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )
        return rows.data or []

    def insert_memory(self, user_id: str, content: str, memory_type: str, metadata: dict[str, Any], embedding: list[float]) -> dict[str, Any] | None:
        fingerprint = sha256(f"{user_id}\n{content.strip().casefold()}".encode("utf-8")).hexdigest()
        existing = (
            self.client.table("creatoros_memories")
            .select("id,content,memory_type,metadata,created_at")
            .eq("external_user_id", user_id)
            .eq("fingerprint", fingerprint)
            .limit(1)
            .execute()
        )
        if existing.data:
            return None
        row = {
            "external_user_id": user_id,
            "content": content.strip(),
            "memory_type": memory_type,
            "metadata": metadata,
            "embedding": embedding,
            "fingerprint": fingerprint,
        }
        result = self.client.table("creatoros_memories").insert(row).execute()
        return result.data[0]

    def search_memories(self, user_id: str, embedding: list[float], top_k: int, min_score: float) -> list[dict[str, Any]]:
        result = self.client.rpc("match_creatoros_memories", {"query_embedding": embedding, "match_user_id": user_id, "match_count": top_k, "min_similarity": min_score}).execute()
        return result.data or []

    def list_memories(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        result = (
            self.client.table("creatoros_memories")
            .select("id,content,memory_type,metadata,created_at")
            .eq("external_user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
