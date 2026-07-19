import os
from typing import Any


def database_config() -> dict[str, Any]:
    return {
        "host": os.getenv("MYSQL_HOST", "mysql"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "seewo"),
        "password": os.getenv("MYSQL_PASSWORD", "seewo_password"),
        "database": os.getenv("MYSQL_DATABASE", "seewo_smart_teaching"),
        "autocommit": False,
    }


def qwen_vl_config() -> dict[str, str | None]:
    return {
        "api_key": os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_VL_API_KEY"),
        "endpoint": os.getenv(
            "QWEN_VL_ENDPOINT",
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        ),
        "model": os.getenv("QWEN_VL_MODEL", "qwen-vl-max-latest"),
    }
