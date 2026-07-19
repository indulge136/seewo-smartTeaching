import asyncio
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.agents.homework_react import HomeworkReActAgent, build_homework_react_system_prompt
from app.grading.skills import load_skill_instruction, route_grading_skill
import app.routes.grading as grading_routes
from app.main import app


client = TestClient(app)


def test_analyze_homework_requires_jpg_or_png() -> None:
    response = client.post(
        "/api/grading/analyze-homework",
        files={"file": ("homework.pdf", b"not-an-image", "application/pdf")},
    )

    assert response.status_code == 400
    assert "仅支持 JPG、PNG 图片" in response.json()["detail"]


def test_analyze_homework_reports_missing_qwen_api_key(monkeypatch) -> None:
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_VL_API_KEY", raising=False)

    response = client.post(
        "/api/grading/analyze-homework",
        files={"file": ("homework.png", b"image-bytes", "image/png")},
        data={"subject": "数学"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Qwen-VL API Key 未配置"


def test_analyze_homework_returns_first_three_grading_stages(monkeypatch) -> None:
    async def fake_qwen_vl(*, image_bytes: bytes, content_type: str, subject: str) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": """
                        {
                          "trusted_question": {
                            "subject": "math",
                            "question": "find quadratic maximum",
                            "student_answer": "x=1 is maximum",
                            "knowledge": ["quadratic function"],
                            "question_type": "calculation",
                            "confidence": 0.96
                          },
                          "grading": {
                            "score": 82,
                            "max_score": 100,
                            "judgement": "partially_correct",
                            "process_score": 32,
                            "result_score": 50,
                            "comments": [
                              {"kind": "concept", "status": "ok", "detail": "formula choice is correct"},
                              {"kind": "process", "status": "warn", "detail": "one intermediate step is missing"},
                              {"kind": "calculation", "status": "warn", "detail": "sign error in the second step"},
                              {"kind": "result", "status": "warn", "detail": "final unit is missing"},
                              {"kind": "format", "status": "ok", "detail": "answer format is readable"}
                            ]
                          },
                          "diagnosis": {
                            "error_causes": [
                              {"kind": "expression_format_issue", "evidence": "final answer missing unit", "severity": "medium"}
                            ],
                            "knowledge_points": ["quadratic function"],
                            "ability_tags": [
                              {"kind": "concept_understanding", "level": "medium"},
                              {"kind": "process_expression", "level": "weak"}
                            ],
                            "student_profile_delta": {
                              "mastery_trend": "stable",
                              "high_frequency_error": "incomplete expression"
                            }
                          }
                        }
                        """
                    }
                }
            ]
        }

    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-key")
    monkeypatch.setattr(grading_routes, "analyze_with_qwen_vl", fake_qwen_vl)

    response = client.post(
        "/api/grading/analyze-homework",
        files={"file": ("homework.jpg", b"image-bytes", "image/jpeg")},
        data={"subject": "math"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"].startswith("\u524d\u4e09\u9636\u6bb5")
    assert set(payload["stages"].keys()) == {"perception", "grading", "diagnosis"}
    assert payload["stages"]["perception"]["trusted_question"]["confidence"] == 0.96
    assert payload["stages"]["grading"]["routing"]["skill"] == "ReasoningSkill"
    assert payload["stages"]["grading"]["score"] == 82
    assert payload["stages"]["grading"]["comments"][0]["kind"] == "concept"
    assert payload["stages"]["diagnosis"]["error_causes"][0]["kind"] == "expression_format_issue"
    assert payload["stages"]["diagnosis"]["ability_tags"][1]["kind"] == "process_expression"
    assert "feedback" not in payload["stages"]


def test_skill_routing_matches_document_question_types() -> None:
    assert route_grading_skill({"question_type": "客观题", "subject": "数学"})["skill"] == "ObjectiveSkill"
    assert route_grading_skill({"question_type": "计算题", "subject": "数学"})["skill"] == "ReasoningSkill"
    assert route_grading_skill({"question_type": "作文", "subject": "语文"})["skill"] == "RubricSkill"
    assert route_grading_skill({"question_type": "图文混合题", "subject": "物理"})["skill"] == "VisionSkill"





def test_homework_react_system_prompt_defines_agent_contract() -> None:
    prompt = build_homework_react_system_prompt("\u6570\u5b66")

    assert "ReAct" in prompt
    assert "Thought" in prompt
    assert "Action" in prompt
    assert "Observation" in prompt
    assert "HomeworkPerceptionSkill" in prompt
    assert "ObjectiveSkill" in prompt
    assert "ReasoningSkill" in prompt
    assert "RubricSkill" in prompt
    assert "VisionSkill" in prompt
    assert "HomeworkDiagnosisSkill" in prompt
    assert "\u4e0d\u8981\u751f\u6210\u4e2a\u6027\u5316\u53cd\u9988" in prompt


def test_homework_perception_skill_is_loaded_from_project_skills_folder() -> None:
    instruction = load_skill_instruction("HomeworkPerceptionSkill")

    assert "Homework Perception" in instruction
    assert "Output Contract" in instruction
    assert "trusted_question" in instruction
    assert "Do not grade" in instruction


def test_homework_reasoning_skill_is_loaded_from_project_skills_folder() -> None:
    instruction = load_skill_instruction("ReasoningSkill")

    assert "Homework Reasoning Grading" in instruction
    assert "process_score" in instruction
    assert "judgement" in instruction
    assert "Fixed Comment Template" in instruction
    assert "kind" in instruction
    assert "process_expression" in instruction


def test_homework_diagnosis_skill_is_loaded_from_project_skills_folder() -> None:
    instruction = load_skill_instruction("HomeworkDiagnosisSkill")

    assert "Homework Diagnosis" in instruction
    assert "error_causes" in instruction
    assert "student_profile_delta" in instruction
    assert "Fixed Field Template" in instruction
    assert "concept_misunderstanding" in instruction
    assert "ability_tags" in instruction


def test_homework_react_agent_runs_perception_routed_skill_and_diagnosis() -> None:
    calls: list[str] = []

    async def fake_model_client(messages: list[dict]) -> dict:
        rendered = json.dumps(messages, ensure_ascii=False)
        calls.append(rendered)

        if "Action: HomeworkDiagnosisSkill" in rendered:
            return {
                "error_causes": ["\u8868\u8fbe\u89c4\u8303\u95ee\u9898"],
                "knowledge_points": ["\u4e8c\u6b21\u51fd\u6570"],
                "ability_tags": ["\u51fd\u6570\u5efa\u6a21"],
                "student_profile_delta": {"mastery_trend": "stable"},
            }

        if "Action: ReasoningSkill" in rendered:
            return {
                "score": 82,
                "max_score": 100,
                "judgement": "partially_correct",
                "process_score": 32,
                "result_score": 50,
                "comments": ["\u8fc7\u7a0b\u601d\u8def\u57fa\u672c\u6b63\u786e"],
            }

        if "Action: HomeworkPerceptionSkill" in rendered:
            return {
                "trusted_question": {
                    "subject": "\u6570\u5b66",
                    "question": "\u8ba1\u7b97\u4e8c\u6b21\u51fd\u6570\u6700\u5927\u503c",
                    "student_answer": "x=1\u65f6\u6700\u5927",
                    "knowledge": ["\u4e8c\u6b21\u51fd\u6570"],
                    "question_type": "\u8ba1\u7b97\u9898",
                    "confidence": 0.95,
                }
            }

        raise AssertionError(rendered)

    agent = HomeworkReActAgent(model_client=fake_model_client)
    result = asyncio.run(
        agent.run(
            image_bytes=b"image-bytes",
            content_type="image/png",
            subject="\u6570\u5b66",
        )
    )

    assert result["trusted_question"]["confidence"] == 0.95
    assert result["grading"]["score"] == 82
    assert result["diagnosis"]["error_causes"] == ["\u8868\u8fbe\u89c4\u8303\u95ee\u9898"]
    assert len(calls) == 3
    assert "Action: HomeworkPerceptionSkill" in calls[0]
    assert "Action: ReasoningSkill" in calls[1]
    assert "Action: HomeworkDiagnosisSkill" in calls[2]
