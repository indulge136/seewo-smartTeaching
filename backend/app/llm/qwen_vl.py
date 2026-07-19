from typing import Any

import httpx
from fastapi import HTTPException

from app.config import qwen_vl_config


async def call_qwen_vl_chat(messages: list[dict[str, Any]]) -> dict[str, Any]:
    config = qwen_vl_config()

    if not config["api_key"]:
        raise HTTPException(status_code=503, detail="Qwen-VL API Key \u672a\u914d\u7f6e")

    payload = {
        "model": config["model"],
        "messages": messages,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            str(config["endpoint"]),
            headers={
                "Authorization": f"Bearer {config['api_key']}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if response.status_code >= 400:
        upstream_detail = response.text.strip()
        if len(upstream_detail) > 240:
            upstream_detail = upstream_detail[:240] + "..."
        raise HTTPException(
            status_code=502,
            detail=f"Qwen-VL \u89e3\u6790\u670d\u52a1\u8c03\u7528\u5931\u8d25 (upstream {response.status_code}): {upstream_detail}",
        )

    return response.json()
