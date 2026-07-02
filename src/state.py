"""상태 정본 인터페이스. 정본 = Notion DB. P2 dry-run은 EmptyState(콜드스타트).

파생: count(난이도), past_questions(중복방지), review_cue(복습), today_exists(멱등성).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from config import settings


class State(ABC):
    @abstractmethod
    def count(self, category: str) -> int: ...
    @abstractmethod
    def past_questions(self, category: str) -> list[str]: ...
    @abstractmethod
    def review_cue(self) -> dict | None: ...
    @abstractmethod
    def today_exists(self) -> bool: ...


class EmptyState(State):
    """P2 콜드스타트: 이력 없음. Notion 미연동 dry-run 전용."""
    def count(self, category: str) -> int:
        return 0

    def past_questions(self, category: str) -> list[str]:
        return []

    def review_cue(self) -> dict | None:
        return None

    def today_exists(self) -> bool:
        return False


def _is_missing_select_option(e: Exception) -> bool:
    """'select option ... not found for property' 검증 오류인지 판별.

    아직 어떤 select 옵션도 쓰이지 않은 신규 카테고리를 필터할 때 Notion이 내는 400.
    이 특정 오류만 삼키고(=0건 취급) 다른 API 오류는 전파하기 위해 좁게 매칭한다.
    """
    try:
        from notion_client.errors import APIResponseError
    except ImportError:
        return False
    return isinstance(e, APIResponseError) and "not found for property" in str(e)


def resolve_data_source_id(client, db_id: str) -> str:
    """Notion 2025-09 API: DB → data source id 해석(단일 소스 가정, 첫 소스 사용)."""
    db = client.databases.retrieve(database_id=db_id)
    sources = db.get("data_sources", [])
    if not sources:
        raise RuntimeError(f"DB {db_id}에 data source가 없습니다(Notion 2025-09 API).")
    return sources[0]["id"]


class NotionState(State):
    """Notion DB 쿼리로 상태 파생 (정본). category(slug)->표시명 변환해 매칭."""
    def __init__(self, client=None, db_id: str | None = None, ds_id: str | None = None):
        if client is None:
            from notion_client import Client
            client = Client(auth=settings.NOTION_API_KEY)
        self.client = client
        self.db_id = db_id or settings.NOTION_DB_ID
        self._ds_id = ds_id or settings.NOTION_DATA_SOURCE_ID or None

    def _data_source_id(self) -> str:
        if not self._ds_id:
            self._ds_id = resolve_data_source_id(self.client, self.db_id)
        return self._ds_id

    def _query(self, filt: dict, page_size: int = 100) -> list[dict]:
        results, cursor = [], None
        ds_id = self._data_source_id()
        while True:
            kw = {"data_source_id": ds_id, "filter": filt, "page_size": page_size}
            if cursor:
                kw["start_cursor"] = cursor
            resp = self.client.data_sources.query(**kw)
            results.extend(resp.get("results", []))
            if not resp.get("has_more"):
                break
            cursor = resp.get("next_cursor")
        return results

    @staticmethod
    def _question_text(page: dict) -> str:
        rt = page.get("properties", {}).get("Question", {}).get("rich_text", [])
        return "".join(seg.get("plain_text", "") for seg in rt)

    def _daily_in_category(self, category: str) -> list[dict]:
        from config import taxonomy
        disp = taxonomy.display_name(category)
        try:
            return self._query({"and": [
                {"property": "Kind", "select": {"equals": "daily"}},
                {"property": "Category", "select": {"equals": disp}},
            ]})
        except Exception as e:  # noqa: BLE001
            # 아직 이 카테고리로 발행된 적이 없으면 Notion Category select에 해당 옵션이
            # 없어 필터 쿼리가 400(validation_error)을 낸다. 논리적으로 0건이므로 빈 목록.
            # (옵션은 첫 발행 시 페이지 생성으로 자동 추가된다.) 그 외 오류는 그대로 전파.
            if _is_missing_select_option(e):
                return []
            raise

    def count(self, category: str) -> int:
        return len(self._daily_in_category(category))

    def past_questions(self, category: str) -> list[str]:
        pages = self._daily_in_category(category)
        pages.sort(key=lambda p: p.get("created_time", ""), reverse=True)
        return [q for q in (self._question_text(p) for p in pages) if q]

    def review_cue(self) -> dict | None:
        target = (datetime.now(settings.TIMEZONE)
                  - timedelta(days=settings.REVIEW_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
        pages = self._query({"and": [
            {"property": "Kind", "select": {"equals": "daily"}},
            {"property": "Date", "date": {"equals": target}},
        ]})
        if not pages:
            return None
        return {"days_ago": settings.REVIEW_LOOKBACK_DAYS,
                "question": self._question_text(pages[0])}

    def today_exists(self) -> bool:
        today = today_kst()
        pages = self._query({"and": [
            {"property": "Kind", "select": {"equals": "daily"}},
            {"property": "Date", "date": {"equals": today}},
        ]}, page_size=1)
        return len(pages) > 0


def today_kst() -> str:
    return datetime.now(settings.TIMEZONE).strftime("%Y-%m-%d")
