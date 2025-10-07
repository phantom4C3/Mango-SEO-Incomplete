

# Please use async supabase supported by supabase-py-async


# backend/src/clients/supabase_client.py
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import json
import logging
from uuid import UUID, uuid4

from supabase import create_client, AsyncClient
from ..core.config import settings
from ..core.security import get_password_hash
from shared_models.models import (
    Article, ArticleCreate, ArticleUpdate, ArticleStatus,
    Task, TaskCreate, TaskStatus,
    User, UserCreate, UserUpdate
)

logger = logging.getLogger(__name__)

# -------------------------
# Async Query Wrapper
# -------------------------
class AsyncQueryBuilder:
    """Wrapper around Supabase async table queries"""
    def __init__(self, table):
        self._table = table

    def select(self, columns: str = "*") -> "AsyncQueryBuilder":
        self._table = self._table.select(columns)
        return self

    def eq(self, column: str, value: Any) -> "AsyncQueryBuilder":
        self._table = self._table.eq(column, value)
        return self

    def in_(self, column: str, values: List[Any]) -> "AsyncQueryBuilder":
        self._table = self._table.in_(column, values)
        return self

    def gte(self, column: str, value: Any) -> "AsyncQueryBuilder":
        self._table = self._table.gte(column, value)
        return self

    def lte(self, column: str, value: Any) -> "AsyncQueryBuilder":
        self._table = self._table.lte(column, value)
        return self

    async def execute(self) -> Any:
        return await self._table.execute()

# -------------------------
# Async Supabase Client
# -------------------------
class AsyncSupabaseClient:
    def __init__(self):
        self._client: Optional[AsyncClient] = None
        self._is_connected = False

    def connect(self):
        if not self._is_connected:
            self._client = AsyncClient(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            self._is_connected = True
            logger.info("✅ Supabase async client connected.")

    async def from_table(self, table_name: str) -> AsyncQueryBuilder:
        self.connect()
        return AsyncQueryBuilder(self._client.table(table_name))

    # -------------------------
    # Generic fetch helpers
    # -------------------------
    async def fetch_one(self, table_name: str, filters: Optional[Dict[str, Any]] = None, select: str = "*") -> Optional[Dict[str, Any]]:
        qb = await self.from_table(table_name)
        qb = qb.select(select).limit(1)
        if filters:
            for col, val in filters.items():
                if isinstance(val, dict):
                    if "gte" in val: qb = qb.gte(col, val["gte"])
                    if "lte" in val: qb = qb.lte(col, val["lte"])
                else:
                    qb = qb.eq(col, val)
        res = await qb.execute()
        return res.data[0] if res.data else None

    async def fetch_all(self, table_name: str, filters: Optional[Dict[str, Any]] = None, select: str = "*", skip: int = 0, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        qb = await self.from_table(table_name)
        qb = qb.select(select)
        if filters:
            for col, val in filters.items():
                if isinstance(val, dict):
                    if "gte" in val: qb = qb.gte(col, val["gte"])
                    if "lte" in val: qb = qb.lte(col, val["lte"])
                else:
                    qb = qb.eq(col, val)
        if limit is not None:
            qb = qb.limit(limit)
        res = await qb.execute()
        data = res.data or []
        if skip: data = data[skip:]
        return data

    # -------------------------
    # Generic insert/update
    # -------------------------
    async def insert_into(self, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        self.connect()
        res = await self._client.table(table_name).insert(data).execute()
        return res.data or []

    async def update_table(self, table_name: str, filters: Dict[str, Any], updates: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.connect()
        builder = self._client.table(table_name).update(updates)
        for col, val in filters.items():
            builder = builder.eq(col, val)
        res = await builder.execute()
        return res.data or []

    # -------------------------
    # User Operations
    # -------------------------
    async def get_user(self, user_id: UUID) -> Optional[User]:
        data = await self.fetch_one("users", {"id": str(user_id)})
        return User(**data) if data else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        data = await self.fetch_one("users", {"email": email})
        return User(**data) if data else None

    async def create_user(self, user_create: UserCreate) -> User:
        user_data = user_create.dict()
        user_data["id"] = str(uuid4())
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        user_data["created_at"] = datetime.utcnow()
        user_data["updated_at"] = datetime.utcnow()
        created = await self.insert_into("users", user_data)
        return User(**created[0])

    async def update_user(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        updates = user_update.dict(exclude_unset=True)
        updates["updated_at"] = datetime.utcnow()
        updated = await self.update_table("users", {"id": str(user_id)}, updates)
        return User(**updated[0]) if updated else None

    # -------------------------
    # Article Operations
    # -------------------------
    async def get_article(self, article_id: UUID) -> Optional[Article]:
        data = await self.fetch_one("articles", {"id": str(article_id)})
        return Article(**data) if data else None

    async def get_user_articles(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Article]:
        data = await self.fetch_all("articles", {"user_id": str(user_id)}, skip=skip, limit=limit)
        return [Article(**a) for a in data]

    async def create_article(self, article_create: ArticleCreate) -> Article:
        article_data = article_create.dict()
        article_data["id"] = str(uuid4())
        article_data["created_at"] = datetime.utcnow()
        article_data["updated_at"] = datetime.utcnow()
        article_data["status"] = ArticleStatus.PENDING.value
        created = await self.insert_into("articles", article_data)
        return Article(**created[0])

    async def update_article(self, article_id: UUID, article_update: ArticleUpdate) -> Optional[Article]:
        updates = article_update.dict(exclude_unset=True)
        updates["updated_at"] = datetime.utcnow()
        updated = await self.update_table("articles", {"id": str(article_id)}, updates)
        return Article(**updated[0]) if updated else None

    # -------------------------
    # Task Operations
    # -------------------------
    async def get_task(self, task_id: UUID) -> Optional[Task]:
        data = await self.fetch_one("tasks", {"id": str(task_id)})
        return Task(**data) if data else None

    async def get_user_tasks(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Task]:
        data = await self.fetch_all("tasks", {"user_id": str(user_id)}, skip=skip, limit=limit)
        return [Task(**t) for t in data]

    async def create_task(self, task_create: TaskCreate) -> Task:
        task_data = task_create.dict()
        task_data["id"] = str(uuid4())
        task_data["created_at"] = datetime.utcnow()
        task_data["updated_at"] = datetime.utcnow()
        task_data["status"] = TaskStatus.PENDING.value
        created = await self.insert_into("tasks", task_data)
        return Task(**created[0])

    async def update_task(self, task_id: UUID, status: TaskStatus, result: Optional[Dict] = None) -> Optional[Task]:
        updates = {"status": status.value, "updated_at": datetime.utcnow()}
        if result is not None:
            updates["result"] = json.dumps(result)
        updated = await self.update_table("tasks", {"id": str(task_id)}, updates)
        return Task(**updated[0]) if updated else None

    # -------------------------
    # CMS Operations
    # -------------------------
    async def get_cms_integrations(self, user_id: UUID) -> List[Dict]:
        return await self.fetch_all("cms_integrations", {"user_id": str(user_id)})

    async def add_cms_integration(self, user_id: UUID, cms_type: str, credentials: Dict) -> Dict:
        integration_data = {
            "id": str(uuid4()),
            "user_id": str(user_id),
            "cms_type": cms_type,
            "credentials": json.dumps(credentials),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        inserted = await self.insert_into("cms_integrations", integration_data)
        return inserted[0] if inserted else {}

    async def publish_article(self, article_id: UUID, cms_integration_id: UUID) -> bool:
        article = await self.get_article(article_id)
        if not article:
            return False
        cms = await self.fetch_one("cms_integrations", {"id": str(cms_integration_id)})
        if not cms:
            return False
        await self.update_article(article_id, ArticleUpdate(status=ArticleStatus.PUBLISHED))
        return True

    # -------------------------
    # SEO & Audit Helpers
    # -------------------------
    async def get_recent_audits(self, website_url: str, before_timestamp: datetime) -> List[Dict[str, Any]]:
        qb = await self.from_table("seo_audit_results")
        qb = qb.select("*").eq("website_url", website_url)
        res = await qb.execute()
        return [row for row in (res.data or []) if row["created_at"] < before_timestamp]

    async def get_historical_metrics(self, website_url: str, days: int = 30) -> List[Dict[str, Any]]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        qb = await self.from_table("seo_metrics")
        qb = qb.select("*").eq("website_url", website_url)
        res = await qb.execute()
        return [row for row in (res.data or []) if row["created_at"] >= cutoff_date]

    # -------------------------
    # Realtime channel
    # -------------------------
    @property
    def channel(self):
        self.connect()
        return self._client.realtime.channel

# -------------------------
# Global client instance
# -------------------------
supabase_client = AsyncSupabaseClient()
