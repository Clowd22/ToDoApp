"""タスク関連のエンドポイント定義（プレゼンテーション層）。

HTTP の受け口として、リクエストの検証（スキーマ）と
サービス・DAO への委譲だけを担当する。
"""

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Path, Query

from app import classifier
from app.dao.task_dao import task_dao
from app.schemas import TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[dict])
def get_tasks(
    status: Literal["all", "active", "completed"] = Query("all", description="完了状態で絞り込み"),
    priority: Optional[Literal["高", "中", "低"]] = Query(None, description="優先度で絞り込み"),
    category: Optional[str] = Query(None, description="カテゴリで絞り込み"),
) -> list[dict]:
    """タスク一覧を取得する。"""
    tasks = task_dao.list_tasks(status, priority, category)
    return [task.to_dict() for task in tasks]


@router.post("", response_model=dict, status_code=201)
def add_task(body: TaskCreate) -> dict:
    """タスクを追加する。タイトル・内容から優先度とカテゴリを自動判定して保存する。"""
    label = classifier.classify(body.title, body.description or "")
    task = task_dao.create(body.title, body.description or "", label["priority"], label["category"])
    return task.to_dict()


@router.patch("/{task_id}/toggle", response_model=dict)
def toggle_task(task_id: int = Path(..., description="対象タスクのID")) -> dict:
    """指定したタスクの完了状態を切り替える。"""
    task = task_dao.toggle(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"タスク(id={task_id})が見つかりません")
    return task.to_dict()


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int = Path(..., description="対象タスクのID")) -> None:
    """指定したタスクを削除する。"""
    if not task_dao.delete(task_id):
        raise HTTPException(status_code=404, detail=f"タスク(id={task_id})が見つかりません")
