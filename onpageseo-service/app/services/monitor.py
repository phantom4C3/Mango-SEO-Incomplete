# onpageseo-service/app/services/monitor.py
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta 
from shared_models.models import MonitoringData, SEOAuditResult, DeploymentResult
from ..clients.supabase_client import supabase_client
from ..clients.api_clients import GA4Client, GoogleSearchConsoleClient
from ..core.config import get_settings

logger = logging.getLogger(__name__)


class SEOMonitor:
    """Service that tracks SEO performance and improvements over time"""

    def __init__(self): 
        self.supabase = supabase_client
        self.settings = get_settings()
        self.gsc_client = GoogleSearchConsoleClient(service_account_json=self.settings.google_service_account_json, site_url=self.settings.site_url)
        self.ga_client = GA4Client()
        
    async def track_deployment_impact(
        self,
        deployment_result: DeploymentResult,
        original_audit: SEOAuditResult,
        website_url: str,
    ) -> MonitoringData:
        """
        Track the impact of SEO deployments over time
        """
        try:
            # Get baseline metrics from before deployment
            baseline_metrics = await self._get_baseline_metrics(
                website_url, original_audit.timestamp
            )

            # Schedule ongoing monitoring
            monitoring_id = await self._schedule_monitoring(
                deployment_result.deployment_id, website_url
            )

            # Return initial monitoring data
            return MonitoringData(
                audit_id=original_audit.audit_id,
                timestamp=datetime.now(),
                metrics_before=baseline_metrics,
                metrics_after={},  # Will be populated later
                improvement_rate=0.0,
                google_search_console_data=None,
                google_analytics_data=None,
            )

        except Exception as e:
            logger.error(f"Monitoring setup failed: {str(e)}")
            raise

    async def _get_baseline_metrics(
        self, website_url: str, audit_timestamp: datetime
    ) -> Dict[str, float]:
        """Get baseline metrics from before deployment"""
        try:
            # Try to get recent audit data
            recent_audits = await self.supabase.get_recent_audits(
                website_url, audit_timestamp
            )
            if recent_audits:
                return recent_audits[0].get("metrics", {})

            # Fallback to current metrics if no recent audit
            return await self._get_current_metrics(website_url)

        except Exception as e:
            logger.warning(f"Could not get baseline metrics: {str(e)}")
            return {}

    async def _get_current_metrics(self, website_url: str) -> Dict[str, float]:
        """Get current SEO metrics from various sources"""
        metrics = {}

        try:
            # Google Search Console data
           gsc_data = await self.gsc_client.get_metrics(website_url)
           metrics.update({
                "impressions": gsc_data.get("impressions", 0),
                "clicks": gsc_data.get("clicks", 0),
                "ctr": gsc_data.get("ctr", 0),
                "average_position": gsc_data.get("position", 0),
            })


        except Exception as e:
            logger.warning(f"Could not get GSC metrics: {str(e)}")

        try:
            # Google Analytics data 
            ga_data = await self.ga_client.get_traffic_data(url_path=website_url)
            metrics.update({
                "sessions": ga_data.get("sessions", 0),
                "bounce_rate": ga_data.get("bounceRate", 0),
                "avg_session_duration": ga_data.get("avgSessionDuration", 0),
            })
        except Exception as e:
            logger.warning(f"Could not get GA metrics: {str(e)}")

        return metrics

    async def _schedule_monitoring(self, deployment_id: str, website_url: str) -> str:
        """Schedule ongoing monitoring for a deployment"""
        monitoring_id = f"mon_{deployment_id}"

        # Schedule regular monitoring checks
        monitoring_job = {
            "monitoring_id": monitoring_id,
            "deployment_id": deployment_id,
            "website_url": website_url,
            "schedule": [
                {"interval": "1h", "duration": "24h"},  # Hourly for first day
                {"interval": "6h", "duration": "7d"},  # Every 6 hours for week
                {"interval": "24h", "duration": "30d"},  # Daily for month
            ],
            "active": True,
            "created_at": datetime.now().isoformat(),
        }

        await self.supabase.store_monitoring_job(monitoring_job)
        return monitoring_id

    async def run_monitoring_check(
        self, monitoring_id: str
    ) -> Optional[MonitoringData]:
        """Run a scheduled monitoring check"""
        try:
            job = await self.supabase.get_monitoring_job(monitoring_id)
            if not job or not job.get("active"):
                return None

            # Get current metrics
            current_metrics = await self._get_current_metrics(job["website_url"])

            # Get previous metrics for comparison
            previous_data = await self.supabase.get_latest_monitoring_data(
                monitoring_id
            )

            # Calculate improvements
            improvement_rate = self._calculate_improvement_rate(
                previous_data.get("metrics_before", {}) if previous_data else {},
                current_metrics,
            )

            # Store monitoring data
            monitoring_data = MonitoringData(
                audit_id=job.get("audit_id", ""),
                timestamp=datetime.now(),
                metrics_before=(
                    previous_data.get("metrics_before", {}) if previous_data else {}
                ),
                metrics_after=current_metrics,
                improvement_rate=improvement_rate,
                google_search_console_data=await self.gsc_client.get_metrics(job["website_url"]),
                google_analytics_data=await self.ga_client.get_traffic_data(
                    job["website_url"]
                ),
            )

            await self.supabase.store_monitoring_data(monitoring_data)
            return monitoring_data

        except Exception as e:
            logger.error(f"Monitoring check failed for {monitoring_id}: {str(e)}")
            return None

    def _calculate_improvement_rate(
        self, metrics_before: Dict, metrics_after: Dict
    ) -> float:
        """Calculate overall improvement rate across metrics"""
        if not metrics_before or not metrics_after:
            return 0.0

        improvements = []

        # CTR improvement (higher is better)
        if "ctr" in metrics_before and "ctr" in metrics_after:
            improvements.append(
                (metrics_after["ctr"] - metrics_before["ctr"])
                / max(metrics_before["ctr"], 0.01)
            )

        # Position improvement (lower is better)
        if "average_position" in metrics_before and "average_position" in metrics_after:
            improvements.append(
                (metrics_before["average_position"] - metrics_after["average_position"])
                / max(metrics_before["average_position"], 1)
            )

        # Sessions improvement (higher is better)
        if "sessions" in metrics_before and "sessions" in metrics_after:
            improvements.append(
                (metrics_after["sessions"] - metrics_before["sessions"])
                / max(metrics_before["sessions"], 1)
            )

        return sum(improvements) / len(improvements) * 100 if improvements else 0.0

    async def generate_performance_report(
        self, website_url: str, timeframe_days: int = 30
    ) -> Dict:
        """Generate a comprehensive performance report"""
        report = {
            "website_url": website_url,
            "timeframe": timeframe_days,
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "trends": {},
            "recommendations": [],
        }

        try:
            # Get historical data
            historical_data = await self.supabase.get_historical_metrics(
                website_url, timeframe_days
            )

            # Calculate trends
            report["trends"] = self._analyze_trends(historical_data)

            # Generate recommendations based on trends
            report["recommendations"] = self._generate_trend_recommendations(
                report["trends"]
            )

            # Add summary statistics
            report["summary"] = {
                "total_improvement": self._calculate_total_improvement(historical_data),
                "best_performing_change": self._identify_best_performing_change(
                    historical_data
                ),
                "areas_needing_attention": self._identify_problem_areas(
                    historical_data
                ),
            }

        except Exception as e:
            logger.error(f"Performance report generation failed: {str(e)}")

        return report

    async def monitor_and_reanalyze(self):
        """Monitor website health and trigger re-analysis if needed"""
        try:
            # Get websites with declining SEO scores
            declining_sites = await supabase_client.fetch_all(
                "websites",
                filters={"current_score": "<70"},
                select="id, current_score, last_analysis_date"
            )
            # Sites with score below 70

            for site in declining_sites.data:
                task_id = f"monitor_{site['id']}_{datetime.now().strftime('%Y%m%d')}"
                await self.batch_processor.process_batch_analysis(
                    site["id"], task_id, max_pages=200  # Focused analysis
                )
                logger.info(
                    f"Triggered re-analysis for declining website: {site['id']}"
                )

        except Exception as e:
            logger.error(f"Monitoring re-analysis failed: {str(e)}")
