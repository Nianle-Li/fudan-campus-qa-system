from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


_TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    frontend_dir: Path
    host: str
    port: int
    database_url: str
    demo_mode: bool


def env_flag(value: str | None) -> bool:
    return (value or "").lower() in _TRUE_VALUES


def load_config(env: Mapping[str, str] | None = None) -> AppConfig:
    source = os.environ if env is None else env
    root_dir = Path(__file__).resolve().parents[2]
    return AppConfig(
        root_dir=root_dir,
        frontend_dir=root_dir / "frontend",
        host=source.get("FCQA_HOST", "127.0.0.1"),
        port=int(source.get("FCQA_PORT", source.get("PORT", "8000"))),
        database_url=source.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/fcqa"),
        demo_mode=env_flag(source.get("FCQA_DEMO_MODE")),
    )
