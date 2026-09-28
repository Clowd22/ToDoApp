# スマートTODO管理API 設計書

> このドキュメントは、Python / FastAPI を学び始めたばかりの方を対象に、
> 「このアプリがどう組み立てられているか」「各ファイルが何をしているか」
> 「リクエストが来てから結果が返るまでの流れ」を丁寧に説明します。
>
> 専門用語は初めて出てきたときに（※）で補足し、最後の「用語集」でまとめています。

---

## 1. このアプリは何をするのか

TODO アプリの **API（バックエンド）** です。ブラウザやアプリから HTTP リクエストを送ると、JSON で応答します。

最大の特徴は、タスクを追加するときに**タイトルと内容から「優先度」と「カテゴリ」を自動で判定してくれる**ことです。

| 機能 | メソッドとパス | 説明 |
| --- | --- | --- |
| 一覧取得 | `GET /tasks` | 保存済みタスクの一覧を返す |
| 追加 | `POST /tasks` | タスクを追加。優先度・カテゴリを自動判定して保存 |
| 完了切り替え | `PATCH /tasks/{id}/toggle` | 指定タスクの「完了⇔未完了」を反転 |
| 削除 | `DELETE /tasks/{id}` | 指定タスクを削除 |

---

## 2. 全体像：なぜファイルを分けるのか

### 2-1. ファイル構成

```
fastapi-test/
├── app/                     ← アプリ本体（Python パッケージ）
│   ├── main.py              ← 組み立て・起動
│   ├── routers/
│   │   └── tasks.py         ← 受付（HTTP リクエストの受け口）
│   ├── schemas.py           ← 申込書（入力データの形とルール）
│   ├── classifier.py        ← 判断担当（優先度・カテゴリの判定ロジック）
│   ├── keywords.py          ← 判断マニュアル（判定に使うキーワード）
│   ├── models.py            ← 商品（タスクを表すデータの箱）
│   ├── dao/
│   │   └── task_dao.py      ← 倉庫係（データベースへの出し入れ）
│   └── db.py                ← 倉庫の扉（データベース接続の管理）
├── static/
│   └── index.html           ← ブラウザで動く操作画面
├── docs/
│   └── design.md            ← この設計書
├── requirements.txt         ← 必要なライブラリの一覧
└── todo.db                  ← データベース（SQLite ファイル）
```

### 2-2. 会社にたとえると

コードの分け方を理解するために、**小さな会社**にたとえます。

| 役割 | 会社での例え | ファイル |
| --- | --- | --- |
| 受付 | 窓口。注文を受け取り、内容を確認して担当者に回す | `app/routers/tasks.py` |
| 申込書 | 注文のフォーマット。「この形で書いてください」というルール | `app/schemas.py` |
| 判断担当 | 注文内容から優先度・カテゴリを考える人 | `app/classifier.py` |
| 判断マニュアル | 判断に使うキーワードの一覧表 | `app/keywords.py` |
| 商品 | 注文1件分の情報を入れる箱 | `app/models.py` |
| 倉庫係 | データベースへの出し入れを担当。SQL を書くのはこの人だけ | `app/dao/task_dao.py` |
| 倉庫の扉 | データベースへの接続を開いたり閉じたりする | `app/db.py` |
| 社長 | 会社全体を立ち上げ、各担当者を配置する | `app/main.py` |

### 2-3. なぜ分けるのか（関心の分離）

全部を `main.py` 1ファイルに書くこともできます。しかし、それだと後で直すときに
「どこを直せばいいか分からない」状態になります。

ファイルを分けておくと、**「直したい内容」と「直すファイル」が1対1で対応**します。

| やりたいこと | 直すファイル |
| --- | --- |
| キーワードを追加したい（例：「大至急」を追加） | `keywords.py` だけ |
| タイトルの文字数制限を変えたい | `schemas.py` だけ |
| 判定のルールを変えたい（例：キーワードが無い時は「中」ではなく「低」に） | `classifier.py` だけ |
| データベースを SQLite から別のものに変えたい | `db.py` と `task_dao.py` だけ |

この「1つのファイル・1つの役割」という考え方を、**関心の分離（Separation of Concerns）** といいます。
これは Python に限らず、ASP.NET Core など他のフレームワークでも共通する大切な考え方です。

---

## 3. 各ファイルの役割（1つずつ丁寧に）

### 3-1. `app/main.py` — 社長（組み立て・起動）

Web サーバー本体（FastAPI アプリ）を作り、ルーター（受付）を登録して、サーバーを起動します。

```python
from fastapi import FastAPI
from app import db
from app.routers import tasks

# Web サーバー本体を作る（会社を設立する）
app = FastAPI(
    title="スマートTODO管理API",
    version="1.0.0",
)

# データベースの準備（倉庫を片付けておく）
db.init_db()

# 受付（tasks ルーター）を雇う
app.include_router(tasks.router)
```

- `app = FastAPI(...)` … Web アプリの本体（※）。ここに色々な機能を登録していく。
- `app.include_router(...)` … 「受付係を雇う」行為。ここで `app/routers/tasks.py` のルーターを登録する。
- `if __name__ == "__main__":` 以下は「このファイルを直接実行したときだけサーバーを起動する」ための定番の書き方。

### 3-2. `app/routers/tasks.py` — 受付（エンドポイント）

HTTP リクエストの受け口です。このファイルの役割は、**できる限り「丸投げ」すること**。

- 入力の形を確認する → スキーマ（`schemas.py`）に任せる
- 優先度・カテゴリの判定 → サービス（`classifier.py`）に任せる
- 保存・取得・削除 → DAO（`task_dao.py`）に任せる

```python
from fastapi import APIRouter, HTTPException
from app import classifier
from app.dao.task_dao import task_dao
from app.schemas import TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])   # この受付は「/tasks」担当

@router.post("", response_model=dict, status_code=201)
def add_task(body: TaskCreate) -> dict:
    # 1. 判定担当に「優先度・カテゴリ」を考えてもらう
    label = classifier.classify(body.title, body.description or "")
    # 2. 倉庫係に「保存」してもらう
    task = task_dao.create(body.title, body.description or "", label["priority"], label["category"])
    # 3. 結果を JSON にして返す
    return task.to_dict()
```

**デコレータ（`@router.post` など）の見方**

`@router.post("")` という行は、「この関数は `POST /tasks` でアクセスされたときに呼びますよ」という目印です。

| デコレータ | 意味 |
| --- | --- |
| `@router.get("")` | `GET /tasks` が来たら呼ぶ |
| `@router.post("")` | `POST /tasks` が来たら呼ぶ |
| `@router.patch("/{task_id}/toggle")` | `PATCH /tasks/123/toggle` が来たら呼ぶ |
| `@router.delete("/{task_id}")` | `DELETE /tasks/123` が来たら呼ぶ |

### 3-3. `app/schemas.py` — 申込書（入力データの形とルール）

「リクエストの JSON がどんな形で、どんなルールを満たすべきか」を定義します。
Python では **Pydantic（※）** というライブラリを使うのが定番です。

```python
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)      # 1〜100文字
    description: Optional[str] = Field("", max_length=500)      # 最大500文字・省略可
```

- `BaseModel` … 「入力の形を定義するためのひな形」。これの子クラスを作ると、FastAPI が自動で検証してくれる。
- `Field(...)` の `...` … 「この項目は必須」という意味。
- `min_length=1` … タイトルは最低1文字。空っぽはエラーになる。
- `Optional[str]` … 「あってもなくてもよい文字列」。無ければ `""`（空文字）を初期値にする。

> ASP.NET Core の `DataAnnotations`（`[Required]` や `[StringLength(100)]`）と同じ役割です。

### 3-4. `app/models.py` — 商品（エンティティ）

「タスク」という **データの入れ物（エンティティ ※）** を定義します。
データベースの1行分の情報を、プログラム内で扱いやすい形にしたものです。

```python
from dataclasses import dataclass

@dataclass
class Task:
    id: int          # 番号
    title: str       # タイトル
    description: str # 詳細
    priority: str    # 優先度（高・中・低）
    category: str    # カテゴリ
    completed: bool  # 完了したか（True / False）
    created_at: str  # 作成日時

    def to_dict(self) -> dict:
        """API が返す JSON の形に変換する。"""
        return {
            "id": self.id,
            "title": self.title,
            # ...
        }
```

- `@dataclass` … 「単なるデータの箱」を簡単に作るための Python の機能。書いた順に値を入れるだけで、`task.id` のようにドットで取り出せるようになる。
- ここは「タスクとは何か」だけを表し、データベースや API の都合は書かないのがポイント。

### 3-5. `app/classifier.py` — 判断担当（サービス層）

優先度・カテゴリを判定する**ビジネスロジック（※）**だけを書きます。
「どんなキーワードを使うか」というデータは書かず、別ファイル（`keywords.py`）から借りてきます。

```python
from app import keywords

def detect_priority(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in keywords.HIGH_PRIORITY_KEYWORDS):
        return "高"
    if any(k in lowered for k in keywords.LOW_PRIORITY_KEYWORDS):
        return "低"
    return "中"

def classify(title: str, description: str) -> dict:
    text = f"{title} {description}"
    return {
        "priority": detect_priority(text),
        "category": detect_category(text),
    }
```

- ここが「頭脳」にあたる部分。判定のルールを変えたいときは、このファイルを直す。

### 3-6. `app/keywords.py` — 判断マニュアル（キーワードデータ）

判定に使う**キーワードの一覧**だけをまとめたファイルです。ロジック（考え方）とデータ（キーワード）を分けることで、
「キーワードを足したい」ときに `classifier.py` のロジックを触らずに済みます。

```python
HIGH_PRIORITY_KEYWORDS = ["緊急", "至急", "締切", "重要", "バグ", ...]
LOW_PRIORITY_KEYWORDS = ["後で", "いつでも", "急がない", ...]
CATEGORY_KEYWORDS = {
    "仕事": ["会議", "納品", "クライアント", ...],
    "家事": ["掃除", "洗濯", "料理", ...],
    # ...
}
```

### 3-7. `app/dao/task_dao.py` — 倉庫係（DAO）

**データベースへの読み書き（SQL の実行）を、このファイルにだけ集めます。**
他のファイルは「保存して」「一覧ちょうだい」とお願いするだけで、SQL のことは知らなくて済みます。

```python
from app import db
from app.models import Task

class TaskDAO:
    def create(self, title, description, priority, category) -> Task:
        with db.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO tasks (title, description, priority, category, created_at) VALUES (?, ?, ?, ?, ?)",
                (title, description, priority, category, db.utc_now()),
            )
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_task(row)   # DB の行 → Task エンティティに変換
```

- `DAO` = Data Access Object（データアクセスオブジェクト）の略。「データベースと会話する専門の係」です。
- `?` はプレースホルダ。SQL に値を直接埋め込まず、`?` に後から値を渡すことで **SQL インジェクション**を防ぎます。
- `_row_to_task()` は、データベースの「行」を `Task` エンティティに変換するヘルパー関数です。

> ASP.NET Core ではこれが **Repository パターン** に相当します。

### 3-8. `app/db.py` — 倉庫の扉（接続管理）

データベースそのものへの**接続の開閉**と、**テーブルの初期作成**を担当します。

```python
import sqlite3

DB_PATH = Path(__file__).parent.parent / "todo.db"   # データベースファイルの場所

def get_connection():
    conn = sqlite3.connect(DB_PATH)    # 扉を開ける
    conn.row_factory = sqlite3.Row     # 結果を「行」として扱えるようにする
    return conn

def init_db():
    with get_connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tasks (...)")   # テーブルが無ければ作る
```

- `with get_connection() as conn:` という書き方は、処理が終わったら自動で接続を閉じてくれる Python の便利な構文（コンテキストマネージャ）です。

---

## 4. 処理の流れを追ってみよう（POST /tasks の例）

「タスクを追加する」とき、コードは次の順番で動きます。デバッガでブレークポイントを置くなら、この順に止まります。

```
[1] 受付      app/routers/tasks.py  add_task()
[2] 判断担当  app/classifier.py     classify()
[3] 倉庫係    app/dao/task_dao.py   TaskDAO.create()
[4] 倉庫の扉  app/db.py             get_connection()
        ↓
    SQLite（todo.db）に保存
```

### ステップごとの解説

1. **受付（`add_task`）** … リクエストを受け取り、`body` として中身（タイトル・内容）を手に入れる。
2. **判断担当（`classify`）** … タイトル＋内容の文字列から「優先度＝高」「カテゴリ＝仕事」などを決めて返す。
3. **倉庫係（`TaskDAO.create`）** … 受け取った値で `INSERT` 文を実行し、保存された行を `Task` エンティティに変換して返す。
4. **倉庫の扉（`get_connection`）** … データベースへの接続を開いて渡す。

最後に受付が `Task.to_dict()` で JSON に変換し、HTTP レスポンス（ステータス 201）として返します。

---

## 5. 用語集

| 用語 | やさしい説明 |
| --- | --- |
| API | プログラム同士が通信するための窓口。ここでは「タスクを操作する HTTP の窓口」 |
| FastAPI | Python で API を簡単に作れるフレームワーク（部品の集まり） |
| ルーター | HTTP リクエストの受け口。URL と関数を結びつける役割 |
| エンドポイント | 「`POST /tasks`」のような、リクエストの宛先 |
| スキーマ（Pydantic） | 入力データの「形とルール」を定義するもの |
| エンティティ | 「タスク」など、扱いたい対象を表すデータの箱 |
| サービス層 | ビジネスの「考え方・ルール」を書く層（ここでは判定ロジック） |
| DAO / Repository | データベースへの読み書きを一手に引き受ける層 |
| インフラ層 | データベース接続など、土台となる技術的な部分 |
| 関心の分離 | 「1つのファイル・1つの役割」に分ける設計思想 |
| 依存性注入（DI） | 必要な部品を「外から渡す」仕組み。ASP.NET Core では標準装備 |
| SQL | データベースを操作するための言語 |
| プレースホルダ（`?`） | SQL に値を安全に埋め込むための「あとで入れる場所」 |
| JSON | データを文字列でやり取りするための形式 |

---

## 6. ASP.NET Core MVC との対応

ASP.NET Core MVC を勉強中の方へ。今回の FastAPI の分け方は、ASP.NET Core の定番構成とほぼ1対1で対応します。

| FastAPI（このプロジェクト） | ASP.NET Core MVC | 役割 |
| --- | --- | --- |
| `app/routers/tasks.py` | `TasksController` | HTTP の受け口 |
| `app/schemas.py`（Pydantic） | DTO + DataAnnotations | 入力の形と検証 |
| `app/models.py`（`Task`） | ドメインモデル / Entity | データの箱 |
| `app/classifier.py` | `ClassificationService` | ビジネスロジック |
| `app/dao/task_dao.py`（`TaskDAO`） | `ITaskRepository` | データアクセス |
| `app/db.py` | `DbContext`（EF Core） | DB 接続 |
| `app/keywords.py` | `appsettings.json` / 定数 | データ・設定 |
| `app/main.py` | `Program.cs` | 組み立て・DI 登録 |
| FastAPI の `Depends` | コンストラクタ注入 | 依存性注入（DI） |

**一番の違いは「依存性注入（DI）」です。** ASP.NET Core は最初から DI が組み込まれていて、
`Program.cs` で `builder.Services.AddScoped<ITaskRepository, TaskRepository>();` のように登録し、
Controller がコンストラクタで受け取ります。FastAPI も `Depends` を使えば同じことができます
（このプロジェクトでは分かりやすさを優先し、`task_dao = TaskDAO()` を直接 import する形にしています）。

---

## 7. まとめ

- このアプリは **「受付 → 判断担当 → 倉庫係 → データベース」** という一方通行の流れで動く。
- 各ファイルは **1つの役割** に絞っている（関心の分離）。
- 直したい内容に応じて、**直すファイルが明確**になる。
- この分け方は ASP.NET Core の Controller / Service / Repository と同じ考え方。

デバッガで処理の流れを追うときは、まず `add_task`（受付）→ `classify`（判断）→ `TaskDAO.create`（倉庫）→ `get_connection`（扉）の順にブレークポイントを置いてみてください。
