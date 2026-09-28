"""API の入出力を表すスキーマ（Pydantic モデル）。"""

from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    """タスク追加（POST /tasks）のリクエストボディ。"""

    title: str = Field(..., min_length=1, max_length=100, description="タスクのタイトル")
    description: Optional[str] = Field("", max_length=500, description="タスクの詳細（任意）")
