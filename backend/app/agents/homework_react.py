import base64
import json
from typing import Any

from app.grading.json_utils import extract_model_json
from app.grading.skills import SKILL_TOOL_DESCRIPTIONS, build_skill_action_instruction, route_grading_skill
from app.llm.qwen_vl import call_qwen_vl_chat
from app.schemas import TrustedQuestion


NO_PERSONALIZED_FEEDBACK_TEXT = "\u4e0d\u8981\u751f\u6210\u4e2a\u6027\u5316\u53cd\u9988"


def build_homework_react_system_prompt(subject: str) -> str:
    tools = "\n".join(f"- {name}: {description}" for name, description in SKILL_TOOL_DESCRIPTIONS.items())
    return f"""
You are the homework grading ReAct Agent for Seewo Smart Teaching. Current subject: {subject}.

Follow the ReAct pattern:
Thought: decide which stage is being solved.
Action: choose exactly one available Skill.
Action Input: provide JSON input for that Skill.
Observation: read the structured output from that Skill.

Available Skill tools:
{tools}

The stage order is fixed:
1. Action=HomeworkPerceptionSkill: parse the uploaded image into TrustedQuestion.
2. Action=ObjectiveSkill/ReasoningSkill/RubricSkill/VisionSkill: select one grading skill by subject and question_type.
3. Action=HomeworkDiagnosisSkill: produce error causes, knowledge points, ability tags, and student profile delta.

Strict boundaries:
- Only complete perception, grading, and diagnosis.
- {NO_PERSONALIZED_FEEDBACK_TEXT}. Do not generate teaching advice, RAG materials, exercise recommendations, or a fourth feedback stage.
- Do not invent invisible question text, answers, diagrams, or score evidence.
- Output valid JSON only.
""".strip()


def build_qwen_prompt(subject: str) -> str:
    return build_homework_react_system_prompt(subject)


class HomeworkReActAgent:
    def __init__(self, model_client: Any | None = None) -> None:
        self.model_client = model_client or call_qwen_vl_chat

    async def run(self, *, image_bytes: bytes, content_type: str, subject: str) -> dict[str, Any]:
        perception = await self._run_perception(image_bytes=image_bytes, content_type=content_type, subject=subject)
        trusted_question_payload = perception.get("trusted_question", perception)
        trusted_question_payload.setdefault("subject", subject)
        trusted_question_payload.setdefault("question", "")
        trusted_question_payload.setdefault("student_answer", "")
        trusted_question_payload.setdefault("knowledge", [])
        trusted_question_payload.setdefault("question_type", "\u672a\u77e5\u9898\u578b")
        trusted_question_payload.setdefault("confidence", 0.0)
        trusted_question = TrustedQuestion(**trusted_question_payload)

        routing = route_grading_skill(trusted_question.model_dump())
        grading = await self._run_grading(
            trusted_question=trusted_question.model_dump(),
            routing=routing,
            image_bytes=image_bytes,
            content_type=content_type,
            subject=subject,
        )
        diagnosis = await self._run_diagnosis(
            trusted_question=trusted_question.model_dump(),
            grading=grading,
            subject=subject,
        )

        return {
            "trusted_question": trusted_question.model_dump(),
            "grading": grading,
            "diagnosis": diagnosis,
        }

    async def _run_perception(self, *, image_bytes: bytes, content_type: str, subject: str) -> dict[str, Any]:
        image_base64 = base64.b64encode(image_bytes).decode("ascii")
        messages = [
            {"role": "system", "content": build_homework_react_system_prompt(subject)},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Thought: parse the uploaded homework image first.\n"
                            "Action: HomeworkPerceptionSkill\n"
                            f"{build_skill_action_instruction('HomeworkPerceptionSkill')}\n"
                            "Action Input: output trusted_question JSON with subject, question, student_answer, "
                            "knowledge, question_type, and confidence."
                        ),
                    },
                    {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_base64}"}},
                ],
            },
        ]
        return extract_model_json(await self.model_client(messages))

    async def _run_grading(
        self,
        *,
        trusted_question: dict[str, Any],
        routing: dict[str, str],
        image_bytes: bytes,
        content_type: str,
        subject: str,
    ) -> dict[str, Any]:
        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": (
                    "Thought: TrustedQuestion is ready; execute the selected grading Skill.\n"
                    f"Action: {routing['skill']}\n"
                    f"{build_skill_action_instruction(routing['skill'])}\n"
                    f"Action Input: {json.dumps({'trusted_question': trusted_question, 'routing': routing}, ensure_ascii=False)}\n"
                    "Observation: output grading JSON only. Use score, max_score, judgement, process_score, "
                    "result_score, and fixed-template comments."
                ),
            }
        ]
        if routing["skill"] == "VisionSkill":
            image_base64 = base64.b64encode(image_bytes).decode("ascii")
            content.append({"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_base64}"}})

        messages = [
            {"role": "system", "content": build_homework_react_system_prompt(subject)},
            {"role": "user", "content": content},
        ]
        return extract_model_json(await self.model_client(messages))

    async def _run_diagnosis(
        self,
        *,
        trusted_question: dict[str, Any],
        grading: dict[str, Any],
        subject: str,
    ) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": build_homework_react_system_prompt(subject)},
            {
                "role": "user",
                "content": (
                    "Thought: grading is complete; produce the diagnosis stage.\n"
                    "Action: HomeworkDiagnosisSkill\n"
                    f"{build_skill_action_instruction('HomeworkDiagnosisSkill')}\n"
                    f"Action Input: {json.dumps({'trusted_question': trusted_question, 'grading': grading}, ensure_ascii=False)}\n"
                    "Observation: output diagnosis JSON only. Use fixed-template error_causes, "
                    "knowledge_points, ability_tags, and student_profile_delta."
                ),
            },
        ]
        return extract_model_json(await self.model_client(messages))
