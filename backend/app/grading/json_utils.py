import json
import re
from typing import Any

from fastapi import HTTPException


def extract_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise HTTPException(status_code=502, detail="Qwen-VL 返回内容不是有效 JSON")
        return json.loads(match.group(0))


def extract_model_json(raw_result: dict[str, Any]) -> dict[str, Any]:
    if "choices" in raw_result:
        content = raw_result["choices"][0]["message"]["content"]
        return extract_json_object(content)
    return raw_result
