"""SQLite への接続管理（インフラ層）。

接続の取得・テーブル初期化など、DB そのものに関わる処理をここに集約する。
"""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルート直下の todo.db を使う（app/ の親ディレクトリ）
DB_PATH = Path(__file__).parent.parent / "todo.db"


def utc_now() -> str:
    """現在時刻の UTC ISO 文字列を返す。"""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_connection() -> sqlite3.Connection:
    """タスク管理用の DB 接続を返す。行を dict として取得できるよう設定する。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """テーブルが無ければ作成する。"""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT '',
                priority    TEXT    NOT NULL,
                category    TEXT    NOT NULL,
                completed   INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL
            )
            """
        )
