from typing import Any

from app.grading.json_utils import extract_json_object
from app.grading.skills import route_grading_skill
from app.schemas import (
    DiagnosisStage,
    GradingStage,
    HomeworkStages,
    PerceptionStage,
    SkillRouting,
    TrustedQuestion,
)


def _coerce_reasoning_comments(raw_comments: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_comments, list):
        return []

    comments: list[dict[str, Any]] = []
    for item in raw_comments:
        if isinstance(item, dict):
            comments.append(
                {
                    "kind": item.get("kind", "comment"),
                    "status": item.get("status", "observed"),
                    "detail": item.get("detail", ""),
                }
            )
        else:
            comments.append({"kind": "comment", "status": "observed", "detail": str(item)})
    return comments


def _coerce_error_causes(raw_causes: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_causes, list):
        return []

    causes: list[dict[str, Any]] = []
    for item in raw_causes:
        if isinstance(item, dict):
            causes.append(
                {
                    "kind": item.get("kind", "issue"),
                    "evidence": item.get("evidence", ""),
                    "severity": item.get("severity", "medium"),
                }
            )
        else:
            causes.append({"kind": "issue", "evidence": str(item), "severity": "medium"})
    return causes


def _coerce_ability_tags(raw_tags: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_tags, list):
        return []

    tags: list[dict[str, Any]] = []
    for item in raw_tags:
        if isinstance(item, dict):
            tags.append({"kind": item.get("kind", "unknown"), "level": item.get("level", "unknown")})
        else:
            tags.append({"kind": str(item), "level": "unknown"})
    return tags


def normalize_qwen_result(raw_result: dict[str, Any], subject: str) -> HomeworkStages:
    if "choices" in raw_result:
        content = raw_result["choices"][0]["message"]["content"]
        parsed = extract_json_object(content)
    else:
        parsed = raw_result

    trusted_question_payload = parsed.get("trusted_question") or parsed.get("perception") or {}
    trusted_question_payload.setdefault("subject", subject)
    trusted_question_payload.setdefault("question", "")
    trusted_question_payload.setdefault("student_answer", "")
    trusted_question_payload.setdefault("knowledge", [])
    trusted_question_payload.setdefault("question_type", "未知题型")
    trusted_question_payload.setdefault("confidence", 0.0)
    trusted_question = TrustedQuestion(**trusted_question_payload)

    grading_payload = parsed.get("grading") or {}
    diagnosis_payload = parsed.get("diagnosis") or {}
    routing = route_grading_skill(trusted_question.model_dump())

    grading_stage = GradingStage(
        routing=SkillRouting(**routing),
        score=grading_payload.get("score", 0),
        max_score=grading_payload.get("max_score", 100),
        judgement=grading_payload.get("judgement", "pending"),
        process_score=grading_payload.get("process_score"),
        result_score=grading_payload.get("result_score"),
        comments=_coerce_reasoning_comments(grading_payload.get("comments", [])),
    )
    diagnosis_stage = DiagnosisStage(
        error_causes=_coerce_error_causes(diagnosis_payload.get("error_causes", [])),
        knowledge_points=diagnosis_payload.get("knowledge_points", trusted_question.knowledge),
        ability_tags=_coerce_ability_tags(diagnosis_payload.get("ability_tags", [])),
        student_profile_delta=diagnosis_payload.get("student_profile_delta", {})
        if isinstance(diagnosis_payload.get("student_profile_delta", {}), dict)
        else {},
    )

    return HomeworkStages(
        perception=PerceptionStage(trusted_question=trusted_question),
        grading=grading_stage,
        diagnosis=diagnosis_stage,
    )
