from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.database import audit_login, mysql_connection
from app.schemas import StudentLoginRequest, StudentLoginResponse
from app.security import sha256_text


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/student-login", response_model=StudentLoginResponse)
def student_login(payload: StudentLoginRequest, request: Request) -> StudentLoginResponse:
    password_hash = sha256_text(payload.password)

    with mysql_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, username, display_name, role, status
            FROM auth_users
            WHERE username = %s
              AND password_hash = %s
              AND role = 'student'
            LIMIT 1
            """,
            (payload.username, password_hash),
        )
        user: dict[str, Any] | None = cursor.fetchone()

        if not user:
            audit_login(
                cursor,
                user_id=None,
                username=payload.username,
                success=False,
                failure_reason="invalid_credentials",
                request=request,
            )
            raise HTTPException(status_code=401, detail="账号或密码不正确")

        if user["status"] != "active":
            audit_login(
                cursor,
                user_id=user["id"],
                username=payload.username,
                success=False,
                failure_reason="user_not_active",
                request=request,
            )
            raise HTTPException(status_code=403, detail="账号已停用，请联系老师或管理员")

        cursor.execute("UPDATE auth_users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s", (user["id"],))
        audit_login(
            cursor,
            user_id=user["id"],
            username=payload.username,
            success=True,
            failure_reason=None,
            request=request,
        )

        return StudentLoginResponse(
            message="login_ok",
            user={
                "id": user["id"],
                "username": user["username"],
                "displayName": user["display_name"],
                "role": user["role"],
            },
        )
