import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.homework_react import HomeworkReActAgent, build_homework_react_system_prompt, build_qwen_prompt
from app.grading.skills import route_grading_skill
from app.routes.auth import router as auth_router
from app.routes.grading import router as grading_router
from app.services.homework_analysis import analyze_with_qwen_vl


def create_app() -> FastAPI:
    app = FastAPI(title="Seewo Smart Teaching API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(grading_router)

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

__all__ = [
    "HomeworkReActAgent",
    "analyze_with_qwen_vl",
    "app",
    "build_homework_react_system_prompt",
    "build_qwen_prompt",
    "create_app",
    "route_grading_skill",
]
