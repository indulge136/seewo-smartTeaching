from fastapi import HTTPException, UploadFile


def validate_homework_image(file: UploadFile) -> None:
    allowed_content_types = {"image/jpeg", "image/png"}
    allowed_extensions = (".jpg", ".jpeg", ".png")
    filename = file.filename or ""

    if file.content_type not in allowed_content_types and not filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail="\u4ec5\u652f\u6301 JPG\u3001PNG \u56fe\u7247")
