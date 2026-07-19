from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import qwen_vl_config
from app.grading.normalization import normalize_qwen_result
from app.grading.validation import validate_homework_image
from app.schemas import HomeworkAnalysisResponse
from app.services.homework_analysis import analyze_with_qwen_vl


router = APIRouter(prefix="/api/grading", tags=["grading"])


@router.post("/analyze-homework", response_model=HomeworkAnalysisResponse)
async def analyze_homework(
    file: UploadFile = File(...),
    subject: str = Form("\u6570\u5b66"),
) -> HomeworkAnalysisResponse:
    validate_homework_image(file)
    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(status_code=400, detail="\u4e0a\u4f20\u56fe\u7247\u4e0d\u80fd\u4e3a\u7a7a")

    raw_result = await analyze_with_qwen_vl(
        image_bytes=image_bytes,
        content_type=file.content_type or "image/png",
        subject=subject,
    )
    stages = normalize_qwen_result(raw_result, subject)

    return HomeworkAnalysisResponse(
        message="\u524d\u4e09\u9636\u6bb5\u6279\u6539\u5b8c\u6210",
        subject=subject,
        filename=file.filename or "homework-image",
        model=qwen_vl_config()["model"] or "qwen-vl-max-latest",
        pipeline_version="perception-reasoning-diagnosis.v1",
        stages=stages,
    )
