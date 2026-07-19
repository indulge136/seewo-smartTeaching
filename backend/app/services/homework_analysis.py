from typing import Any

from app.agents.homework_react import HomeworkReActAgent


async def analyze_with_qwen_vl(*, image_bytes: bytes, content_type: str, subject: str) -> dict[str, Any]:
    agent = HomeworkReActAgent()
    return await agent.run(image_bytes=image_bytes, content_type=content_type, subject=subject)
