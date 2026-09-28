"""FastAPI アプリの組み立てと起動。

各層をここで束ねる。エンドポイントの実体は app.routers 以下にある。
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.routers import tasks

# プロジェクトルート（app/ の親ディレクトリ）
BASE_DIR = Path(__file__).parent.parent

app = FastAPI(
    title="スマートTODO管理API",
    description="タスクの追加・一覧・完了切り替えができ、優先度とカテゴリを自動判定します。",
    version="1.0.0",
)

db.init_db()

app.include_router(tasks.router)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """ブラウザ操作用の画面を返す。"""
    return FileResponse(BASE_DIR / "static" / "index.html")


app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
