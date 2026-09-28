# スマートTODO管理API

FastAPI で作った TODO 管理 API。タスクを追加すると、タイトルと内容から**優先度（高・中・低）**と**カテゴリ**を自動判定して保存します。

レイヤードアーキテクチャで構成し、責務ごとに層・ファイルを分離しています。詳細は [docs/design.md](docs/design.md) を参照してください。

## 起動方法

```bash
# 仮想環境の作成と依存ライブラリのインストール（初回のみ）
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# サーバー起動
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

起動後、ブラウザで以下にアクセスしてください。

| URL | 内容 |
| --- | --- |
| `http://127.0.0.1:8000/` | ブラウザ操作用の Web 画面 |
| `http://127.0.0.1:8000/docs` | OpenAPI ドキュメント（Swagger UI） |

## エンドポイント

| メソッド | パス | 説明 |
| --- | --- | --- |
| `GET` | `/tasks` | タスク一覧。`?status=active\|completed` `?priority=高\|中\|低` `?category=...` で絞り込み可 |
| `POST` | `/tasks` | タスク追加。`{"title": "...", "description": "..."}` を送ると自動判定して保存 |
| `PATCH` | `/tasks/{id}/toggle` | 指定タスクの完了状態を切り替え |
| `DELETE` | `/tasks/{id}` | 指定タスクを削除 |

## 自動判定の仕組み

- **優先度**: キーワード（緊急・至急・今日・明日・締切・重要・バグ…）があれば「高」、後で・いつでも・急がない… は「低」、それ以外は「中」。
- **カテゴリ**: 仕事・家事・学習・健康・プライベートの各キーワードを数えて最も一致したものを採用。一致が無ければ「その他」。

判定ロジックは `app/classifier.py`、判定に使うキーワードは `app/keywords.py` に集約しているので、キーワードを追加するだけで調整できます。

## ファイル構成

```
app/
├── main.py              # アプリの組み立てと起動
├── schemas.py           # API 入出力のスキーマ（Pydantic）
├── models.py            # エンティティ（Task）
├── classifier.py        # 優先度・カテゴリの自動判定ロジック（サービス層）
├── keywords.py          # 判定キーワードデータ
├── db.py                # SQLite 接続管理（インフラ層）
├── dao/
│   └── task_dao.py      # データアクセス層（DAO）
└── routers/
    └── tasks.py         # エンドポイント定義（プレゼンテーション層）
static/index.html        # ブラウザ操作用の Web 画面
docs/design.md           # 設計書
requirements.txt         # 依存ライブラリ
```

## 補足

- データは SQLite ファイル `todo.db` に保存されるため、サーバーを再起動しても消えません。初期化したい場合は `todo.db` を削除してください。
- 起動時にアプリを直接実行する場合（`.venv/bin/python -m app.main`）も、`--reload` 付きで同じように起動します。
