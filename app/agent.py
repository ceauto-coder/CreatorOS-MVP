from agents import Agent, Runner
from .config import get_settings


SYSTEM_PROMPT = """
You are Creator Host, the strategic AI copilot inside CreatorOS.
You help creators turn ideas into concrete content, campaigns and marketing actions.
Be practical, concise and decisive. Use the creator's persistent memories and recent
conversation context when supplied, but never claim a memory exists unless it is in context.
If the request is ambiguous, make the most useful reasonable assumption and state it briefly.
Answer in Spanish unless the user writes in another language.
""".strip()


def build_agent(memory_context: str = "", recent_history: str = "") -> Agent:
    settings = get_settings()
    instructions = SYSTEM_PROMPT
    if memory_context:
        instructions += "\n\nPERSISTENT CREATOR MEMORY:\n" + memory_context
    if recent_history:
        instructions += "\n\nRECENT CONVERSATION HISTORY:\n" + recent_history
    return Agent(name="Creator Host", instructions=instructions, model=settings.creatoros_model)


async def run_creator_host(message: str, memory_context: str = "", recent_history: str = "") -> str:
    agent = build_agent(memory_context, recent_history)
    result = await Runner.run(agent, message, max_turns=8)
    return str(result.final_output)
