import asyncio
import sys
from pathlib import Path

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.llm.qwen_vl import call_qwen_vl_chat


class FakeQwenResponse:
    status_code = 400
    text = '{"code":"InvalidApiKey","message":"invalid api-key"}'


class FakeAsyncClient:
    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, *args, **kwargs) -> FakeQwenResponse:
        return FakeQwenResponse()


def test_qwen_client_exposes_safe_upstream_error(monkeypatch) -> None:
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr("app.llm.qwen_vl.httpx.AsyncClient", FakeAsyncClient)

    try:
      asyncio.run(call_qwen_vl_chat([{"role": "user", "content": "test"}]))
    except HTTPException as exc:
        assert exc.status_code == 502
        assert "Qwen-VL 解析服务调用失败" in exc.detail
        assert "400" in exc.detail
        assert "InvalidApiKey" in exc.detail
    else:
        raise AssertionError("Expected HTTPException")
