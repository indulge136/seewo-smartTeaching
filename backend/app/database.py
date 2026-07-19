from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from fastapi import Request

from app.config import database_config


@contextmanager
def mysql_connection() -> Iterator[mysql.connector.MySQLConnection]:
    connection = mysql.connector.connect(**database_config())
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def audit_login(
    cursor: mysql.connector.cursor.MySQLCursorDict,
    *,
    user_id: int | None,
    username: str,
    success: bool,
    failure_reason: str | None,
    request: Request,
) -> None:
    cursor.execute(
        """
        INSERT INTO login_audit_logs (
          user_id, username, role_attempted, success, failure_reason, ip_address, user_agent
        ) VALUES (%s, %s, 'student', %s, %s, %s, %s)
        """,
        (
            user_id,
            username,
            success,
            failure_reason,
            request.client.host if request.client else None,
            request.headers.get("user-agent"),
        ),
    )
