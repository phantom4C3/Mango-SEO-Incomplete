
# Please use async supabase supported by supabase-py-async


# onpageseo-service\app\clients\supabase_client.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import concurrent.futures

from supabase import create_client, Client
from ..core.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)


class AsyncQueryBuilder:
    def __init__(self, sync_query_builder):
        self._sync_query_builder = sync_query_builder

    def select(self, columns: str = "*") -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.select(columns)
        return self

    # ✅ FIXED: Correct eq() method
    def eq(self, column: str, value: Any) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.eq(column, value)
        return self
 
    def in_(self, column: str, values: List[Any]) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.filter(column, "in", values)
        return self

    # ✅ ADD: Missing gte() method
    def gte(self, column: str, value: Any) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.gte(column, value)
        return self

    # ✅ ADD: Missing lte() method  
    def lte(self, column: str, value: Any) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.lte(column, value)
        return self

    def delete(self) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.delete()
        return self

    def update(self, data: Dict) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.update(data)
        return self

    def insert(self, data: Dict) -> "AsyncQueryBuilder":
        self._sync_query_builder = self._sync_query_builder.insert(data)
        return self

    async def execute(self) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(_executor, self._sync_query_builder.execute)



class AsyncSupabaseClient:
    def __init__(self):
        self._client: Optional[Client] = None
        self._is_connected = False

    def connect(self):
        """Sync connection (Supabase client is synchronous)."""
        self._client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )
        self._is_connected = True
        logger.info("✅ Supabase connected.")

    async def from_table(self, table_name: str) -> AsyncQueryBuilder:
        if not self._is_connected:
            self.connect()
        return AsyncQueryBuilder(self._client.table(table_name))

    # ✅ FIXED: Consistent method usage
    async def fetch_one(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        select: str = "*",
    ) -> Optional[Dict[str, Any]]:
        qb = await self.from_table(table_name)
        qb = qb.select(select)
        
        if filters:
            for col, val in filters.items():
                if isinstance(val, dict):
                    # handle range filters using proper methods
                    if "gte" in val:
                        qb = qb.gte(col, val["gte"])
                    if "lte" in val:
                        qb = qb.lte(col, val["lte"])
                else:
                    qb = qb.eq(col, val)
        
        res = await qb.execute()
        return res.data[0] if res.data else None

    # ✅ FIXED: Consistent method usage
    async def fetch_all(
        self,
        table_name: str,
        filters: Optional[Dict[str, Any]] = None,
        select: str = "*",
    ) -> List[Dict[str, Any]]:
        qb = await self.from_table(table_name)
        qb = qb.select(select)
        
        if filters:
            for col, val in filters.items():
                if isinstance(val, dict):
                    # handle range filters using proper methods
                    if "gte" in val:
                        qb = qb.gte(col, val["gte"])
                    if "lte" in val:
                        qb = qb.lte(col, val["lte"])
                else:
                    qb = qb.eq(col, val)
        
        res = await qb.execute()
        return res.data or []

    async def insert_into(
        self, table_name: str, data: Dict[str, Any] | List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        qb = await self.from_table(table_name)
        qb = qb.insert(data)
        res = await qb.execute()
        return res.data or []

    async def update_table(
        self, table_name: str, filters: Dict[str, Any], updates: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        qb = await self.from_table(table_name)
        for col, val in filters.items():
            qb = qb.eq(col, val)
        qb = qb.update(updates)
        res = await qb.execute()
        return res.data or []

    # ✅ FIXED: Method chaining and table name
    async def get_recent_audits(
        self, website_url: str, before_timestamp: datetime
    ) -> List[Dict[str, Any]]:
        qb = await self.from_table("seo_audit_results")  # Use correct table name from schema
        qb = qb.select("*").eq("website_url", website_url)
        res = await qb.execute()
        return [row for row in (res.data or []) if row["created_at"] < before_timestamp]

    # ✅ FIXED: Method chaining
    async def get_historical_metrics(
        self, website_url: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        qb = await self.from_table("seo_metrics")
        qb = qb.select("*").eq("website_url", website_url)
        res = await qb.execute()
        return [row for row in (res.data or []) if row["created_at"] >= cutoff_date]


# Global client instance
supabase_client = AsyncSupabaseClient()