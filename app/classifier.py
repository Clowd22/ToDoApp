"""タスクのタイトル・内容から優先度とカテゴリを自動判定するロジック（サービス層）。

判定に使うキーワードは app.keywords に分離している。
"""

from app import keywords


def detect_priority(text: str) -> str:
    """タイトル・内容の文字列から優先度を判定する（高・中・低）。"""
    lowered = text.lower()
    if any(keyword in lowered for keyword in keywords.HIGH_PRIORITY_KEYWORDS):
        return keywords.PRIORITY_HIGH
    if any(keyword in lowered for keyword in keywords.LOW_PRIORITY_KEYWORDS):
        return keywords.PRIORITY_LOW
    return keywords.PRIORITY_MEDIUM


def detect_category(text: str) -> str:
    """タイトル・内容の文字列からカテゴリを判定する。"""
    lowered = text.lower()
    best_category = keywords.DEFAULT_CATEGORY
    best_score = 0
    for category, category_keywords in keywords.CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in category_keywords if keyword in lowered)
        if score > best_score:
            best_score = score
            best_category = category
    return best_category


def classify(title: str, description: str) -> dict:
    """タイトルと内容から優先度とカテゴリをまとめて判定する。"""
    text = f"{title} {description}".strip()
    return {
        "priority": detect_priority(text),
        "category": detect_category(text),
    }
