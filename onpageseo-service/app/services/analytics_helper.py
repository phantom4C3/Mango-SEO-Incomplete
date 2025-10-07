# onpageseo-service/app/services/analytics_helper.py

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
from ..clients.api_clients import api_clients
from ..clients.supabase_client import supabase_client
from urllib.parse import urlparse 

logger = logging.getLogger(__name__)


class AnalyticsHelper:
    """
    Unified access to analytics data:
    - Can fetch live metrics from APIs.
    - Optionally fetch historical metrics from Supabase.
    - Optional explicit DB save for historical tracking.
    """

    # -------------------
    # Low-level fetchers (LIVE ONLY)
    # -------------------
        
    @staticmethod
    async def get_pagespeed_metrics(url: str) -> Dict[str, Any]:
        try:
            data = await api_clients["pagespeed"].get_metrics(url)
            if not data:
                logger.warning(f"PageSpeed returned empty data for {url}")
            else:
                logger.info(f"[Live Fetch] PageSpeed metrics for {url}: {data}")
            return data or {}
        except Exception as e:
            logger.error(f"PageSpeed API fetch failed for {url}: {e}", exc_info=True)
            return {}

    @staticmethod
    async def get_ga_metrics(url: str) -> Dict[str, Any]:
        try:
            
            path = urlparse(url).path or "/"  # default to "/" if empty
            data = await api_clients["ga4"].get_traffic_data(path)

            if not data:
                logger.warning(f"GA4 returned empty data for {url}")
            else:
                logger.info(f"[Live Fetch] GA4 metrics for {url}: {data}")
            return data or {}
        except Exception as e:
            logger.error(f"GA API fetch failed for {url}: {e}", exc_info=True)
            return {}

    @staticmethod
    async def get_serp_metrics(query: str, location: str = "us") -> Dict[str, Any]:
        try:
            data = await api_clients["serp"].get_keyword_ranks(f"{query} {location}")
            if not data:
                logger.warning(f"SERP API returned empty data for query '{query}' in {location}")
            else:
                logger.info(f"[Live Fetch] SERP metrics for '{query}': {data}")
            return data or {}
        except Exception as e:
            logger.error(f"SERP API fetch failed for {query}: {e}", exc_info=True)
            return {}


    # -------------------
    # High-level wrapper
    # -------------------

    @staticmethod
    async def get_current_metrics(
        url: str,
        url_id: Optional[str] = None,
        keyword: Optional[str] = None,
        location: str = "us",
        force_live: bool = True,
        save_history: bool = False,
    ) -> Dict[str, Any]:
        """
        Unified snapshot of current metrics.
        - force_live=True -> always fetch from APIs.
        - save_history=True -> optionally store snapshot in Supabase.
        """
        results = {}

        if force_live:
            # always fetch live metrics
            results["pagespeed"] = await AnalyticsHelper.get_pagespeed_metrics(url)
            results["ga"] = await AnalyticsHelper.get_ga_metrics(url)
            if keyword:
                results["serp"] = await AnalyticsHelper.get_serp_metrics(keyword, location)
        else:
            # fallback: try DB first (optional, if you want)
            # you can implement cached DB fallback here if needed
            results["pagespeed"] = await AnalyticsHelper.get_pagespeed_metrics(url)
            results["ga"] = await AnalyticsHelper.get_ga_metrics(url)
            if keyword:
                results["serp"] = await AnalyticsHelper.get_serp_metrics(keyword, location)

        # optionally save historical snapshot
        if save_history and url_id:
            await AnalyticsHelper.save_performance_snapshot(url_id, results)

        return results

    @staticmethod
    async def get_historical_metrics(url_id: str, days: int = 90) -> List[Dict[str, Any]]:
        """Fetch stored historical metrics from Supabase."""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            res = (
                supabase_client.client
                .from_("performance_history")
                .select("metrics, fetched_at")
                .gte("fetched_at", start_date.isoformat())
                .lte("fetched_at", end_date.isoformat())
                .eq("url_id", url_id)
                .execute()
            )
            return res.data if res.data else []

        except Exception as e:
            logger.error(f"Failed to fetch historical metrics for {url_id}: {e}")
            return []

    # -------------------
    # Explicit historical save (optional)
    # -------------------

    @staticmethod
    async def save_performance_snapshot(url_id: str, metrics: Dict[str, Any]):
        """Explicitly save current metrics into performance_history."""
        try:
            await supabase_client.insert_into("performance_history", {
                "url_id": url_id,
                "metrics": metrics,
                "fetched_at": datetime.utcnow().isoformat()
            })
            logger.info(f"Saved performance snapshot for {url_id}")
        except Exception as e:
            logger.error(f"Failed to save performance snapshot for {url_id}: {e}")
