import json
import logging
import time
from typing import Dict, Any

from ..clients.ai_clients import gemini_client
from shared_models.models import AgentResult, AgentType

logger = logging.getLogger(__name__)


class PerformanceAgent:
    """Analyzes website performance metrics and predicts SEO impact."""

    def __init__(self):
        self.default_backoff: int = 2
        self.max_retries: int = 3
        self.ai_client = gemini_client  # use shared Gemini client


    async def analyze_performance(
        self, current_metrics: Dict[str, Any], historical_metrics: Dict[str, Any]
    ) -> AgentResult:
        """
        Main entrypoint called from recommender.py.
        Collects current & historical data, predicts SEO impact.
        """
        start_time = time.perf_counter()

        try:
            current_metrics = current_metrics or {}
            historical_metrics = historical_metrics or {}

            logger.info(f"[PerformanceAgent] Current metrics: {current_metrics}")
            logger.info(f"[PerformanceAgent] Historical metrics: {historical_metrics}")

            prediction = await self._predict_performance_impact(
                current_data=current_metrics,
                historical_data=historical_metrics,
            )

            processing_time = round(time.perf_counter() - start_time, 3)

            return AgentResult(
                agent_type=AgentType.PERFORMANCE,
                input_data={
                    "current_metrics": current_metrics,
                    "historical_metrics": historical_metrics,
                },
                output_data=prediction,
                processing_time=processing_time,
                confidence_score=0.9 if prediction else 0.0,
                cost_estimate=0,
                tokens_used=0,
            )

        except Exception as e:
            logger.error(f"PerformanceAgent failed: {str(e)}", exc_info=True)
            return self._create_fallback_result()

    async def _predict_performance_impact(
        self, current_data: Dict[str, Any], historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Predict SEO performance impact using AI.
        Returns a dict with keys:
        - traffic_prediction
        - timeline
        - mobile_desktop_impact
        - risk_assessment
        - roi_estimate
        - competitor_impact
        """
        try:
            prompt = f"""
            You are an SEO and web performance analysis AI.

            Based on the following metrics provided by the user:

            Current Website Metrics: {json.dumps(current_data, indent=2)}
            Historical Metrics (last 90 days): {json.dumps(historical_data, indent=2)}

            Analyze the data and predict SEO and website performance impact, including:

            1. Expected traffic change (%) 
            2. Ranking improvement timeline 
            3. Mobile and desktop performance impact 
            4. Risk assessment and potential issues 
            5. ROI estimation 
            6. Competitor impact analysis

            Return a JSON object with these keys:
            - traffic_prediction
            - timeline
            - mobile_desktop_impact
            - risk_assessment
            - roi_estimate
            - competitor_impact
            """

            
            response = await self.ai_client.generate_structured(prompt=prompt)

            # Ensure structured dict fallback
            if not isinstance(response, dict):
                response = {
                    "traffic_prediction": None,
                    "timeline": None,
                    "mobile_desktop_impact": None,
                    "risk_assessment": None,
                    "roi_estimate": None,
                    "competitor_impact": None,
                }
            return response if isinstance(response, dict) else {}

        except Exception as e:
            logger.warning(f"AI prediction failed: {str(e)}", exc_info=True)
            return {}

    def _create_fallback_result(self) -> AgentResult:
        """Fallback result when agent fails."""
        return AgentResult(
            agent_type=AgentType.PERFORMANCE,
            input_data={},
            output_data={},
            processing_time=0,
            confidence_score=0.0,
            cost_estimate=0,
            tokens_used=0,
        )
