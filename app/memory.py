from openai import AsyncOpenAI
from .config import get_settings
from .db import Database
from .schemas import MemoryExtraction
from agents import Agent, Runner


MEMORY_EXTRACTOR_PROMPT = """
You are the CreatorOS Memory Extractor.
Decide whether the supplied creator message contains durable, creator-specific information
that will be useful in future conversations. Save preferences, audience, brand details,
recurring goals, constraints, skills, offers, tone preferences, tools they use, and other
stable facts. Do NOT save transient requests, generic facts, one-off ideas, secrets,
passwords, API keys, financial credentials, or sensitive personal data.
Return only the structured output requested by the schema. Create short atomic memories,
written in Spanish unless the source is clearly another language.
""".strip()


class MemoryService:
    def __init__(self, db: Database | None = None) -> None:
        settings = get_settings()
        self.db = db or Database()
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.creatoros_embedding_model
        self.top_k = settings.creatoros_memory_top_k
        self.min_score = settings.creatoros_memory_min_score
        self.extractor_model = settings.creatoros_memory_extractor_model

    async def embed(self, text: str) -> list[float]:
        response = await self.openai.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

    async def retrieve(self, user_id: str, query: str) -> list[dict]:
        embedding = await self.embed(query)
        return self.db.search_memories(user_id, embedding, self.top_k, self.min_score)

    async def remember(self, user_id: str, content: str, memory_type: str = "preference", metadata: dict | None = None) -> dict | None:
        embedding = await self.embed(content)
        return self.db.insert_memory(user_id, content, memory_type, metadata or {}, embedding)

    async def extract_and_save(self, user_id: str, user_message: str, assistant_message: str) -> list[dict]:
        agent = Agent(name="CreatorOS Memory Extractor", instructions=MEMORY_EXTRACTOR_PROMPT, model=self.extractor_model, output_type=MemoryExtraction)
        source = f"CREATOR MESSAGE:\n{user_message}\n\nCREATOR HOST RESPONSE:\n{assistant_message}"
        result = await Runner.run(agent, source, max_turns=2)
        extraction = result.final_output
        if not extraction.should_save or not extraction.memories:
            return []
        saved: list[dict] = []
        for content in extraction.memories[:5]:
            content = content.strip()
            if not content:
                continue
            row = await self.remember(user_id, content, extraction.memory_type, {"source": "automatic_memory_extraction"})
            if row:
                saved.append(row)
        return saved
