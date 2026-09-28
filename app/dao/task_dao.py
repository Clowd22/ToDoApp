"""タスクのデータアクセス層（DAO）。

tasks テーブルへの SQL 実行をここに一元化し、
他の層（ルーター・サービス）は DB の詳細を意識しないようにする。
"""

import sqlite3

from app import db
from app.models import Task


def _row_to_task(row: sqlite3.Row) -> Task:
    """DB の行を Task エンティティへ変換する。"""
    return Task(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=row["priority"],
        category=row["category"],
        completed=bool(row["completed"]),
        created_at=row["created_at"],
    )


class TaskDAO:
    """tasks テーブルへの CRUD 操作を担当するクラス。"""

    def create(self, title: str, description: str, priority: str, category: str) -> Task:
        with db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, priority, category, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, description, priority, category, db.utc_now()),
            )
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        return _row_to_task(row)

    def list_tasks(self, status: str | None, priority: str | None, category: str | None) -> list[Task]:
        """タスク一覧を取得する。絞り込み条件があれば適用する。"""
        query = "SELECT * FROM tasks"
        conditions = []
        params: list = []

        if status == "active":
            conditions.append("completed = 0")
        elif status == "completed":
            conditions.append("completed = 1")
        if priority:
            conditions.append("priority = ?")
            params.append(priority)
        if category:
            conditions.append("category = ?")
            params.append(category)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"

        with db.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [_row_to_task(row) for row in rows]

    def get(self, task_id: int) -> Task | None:
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return _row_to_task(row) if row else None

    def toggle(self, task_id: int) -> Task | None:
        """指定 ID のタスクの完了状態を反転し、更新後のタスクを返す。"""
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT completed FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if row is None:
                return None
            new_value = 0 if row["completed"] else 1
            conn.execute(
                "UPDATE tasks SET completed = ? WHERE id = ?", (new_value, task_id)
            )
            updated = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
        return _row_to_task(updated)

    def delete(self, task_id: int) -> bool:
        """指定 ID のタスクを削除し、削除できたかどうかを返す。"""
        with db.get_connection() as conn:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0


# ルーターから参照しやすいよう、シングルトンとして1つ生成しておく
task_dao = TaskDAO()
