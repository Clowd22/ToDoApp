"""タスクを表すエンティティ（ドメイン層）。"""

from dataclasses import dataclass


@dataclass
class Task:
    """タスク1件分のデータを保持するエンティティ。

    DB の行や API の形式には依存しない純粋なドメインオブジェクトとして定義する。
    DB の行（sqlite3.Row）から Task への変換は DAO 層（app.dao.task_dao）が担う。
    """

    id: int
    title: str
    description: str
    priority: str
    category: str
    completed: bool
    created_at: str

    def to_dict(self) -> dict:
        """API レスポンス用の dict へ変換する。"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "category": self.category,
            "completed": self.completed,
            "created_at": self.created_at,
        }
