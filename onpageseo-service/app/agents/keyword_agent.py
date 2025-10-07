# onpageseo-service/app/agents/keyword_agent.py

import logging
import asyncio
from typing import Dict, List, Any
from pytrends.request import TrendReq

from shared_models.models import AgentResult
from ..clients.ai_clients import gemini_client
from shared_models.models import (
    AgentResult,
    AgentType,
)

logger = logging.getLogger(__name__)


class KeywordAgent:
    """
    Handles keyword-specific analysis:
    - Primary & secondary keyword identification
    - Search intent analysis
    - Seasonal trends (via PyTrends) 
    
    NOTE: Competitor gap analysis & semantic expansion have been removed.
    Those are now handled by CompetitorAgent and SemanticAgent.
    """

    def __init__(self):
        # Thread-safe pytrends client
        self._pytrends = TrendReq(hl="en-US", tz=360)
        self.ai_client = gemini_client  # use shared Gemini client

    async def run(self, url: str, content: str, keywords: List[str]) -> AgentResult:
        """Main entrypoint for keyword analysis."""
        try:
            
            print(f"[KeywordAgent.run] url: {url}, content length: {len(content)}, keywords: {keywords}")

            tasks = [
                self._identify_primary_secondary(keywords),
                self._analyze_search_intent(keywords, content),
                self._fetch_trends(keywords), 
            ]

            (
                primary_secondary,
                search_intent,
                trends, 
            ) = await asyncio.gather(*tasks)

            return AgentResult(
                agent_type=AgentType.KEYWORD,
                input_data={"url": url, "keywords": keywords, "content_length": len(content)},
                output_data={
                    "primary_secondary": primary_secondary,
                    "search_intent": search_intent,
                    "seasonal_trends": trends,
                },
                processing_time=0,  # optionally track
                confidence_score=0.9,
                cost_estimate=0,
                tokens_used=0,
            )


        except Exception as e:
            logger.error(f"KeywordAgent failed: {str(e)}")
            return AgentResult(success=False, data={}, error=str(e))

    # ----------------------------
    # Subtasks
    # ----------------------------

    async def _identify_primary_secondary(self, keywords: List[str]) -> Dict[str, List[str]]:
        """Split keywords into primary/secondary buckets using AI."""
        if not keywords:
            return {"primary": [], "secondary": []}

        prompt = f"""
        Given this keyword list: {keywords}

        Classify into:
        - Primary (most important, high search intent relevance)
        - Secondary (supporting/long-tail)

        Return JSON like:
        {{"primary": ["keyword1", "keyword2"], "secondary": ["keyword3", "keyword4"]}}
        """
        
        print(f"[KeywordAgent._identify_primary_secondary] prompt:\n{prompt}")

        
        try:
            result = await self.ai_client.generate_structured(
                prompt=prompt,  
            )
            print(f"[KeywordAgent._identify_primary_secondary] Gemini response: {result}")

            return result if isinstance(result, dict) else {"primary": [], "secondary": []}
        except Exception as e:
            logger.warning(f"Keyword classification failed: {str(e)}")
            return {"primary": [], "secondary": []}

    async def _analyze_search_intent(self, keywords: List[str], content: str) -> Dict[str, str]:
        """Use AI to map each keyword to search intent (informational, navigational, transactional)."""
        if not keywords:
            return {}

        prompt = f"""
        Analyze the search intent for these keywords in context of the page content:
        Keywords: {keywords}
        Content (excerpt): {content[:500]}

        Return JSON:
        {{"keyword": "intent"}}
        """
        print(f"[KeywordAgent._analyze_search_intent] prompt:\n{prompt}")

        try:
            result = await self.ai_client.generate_structured(
                prompt=prompt, 
            )
            print(f"[KeywordAgent._analyze_search_intent] Gemini response: {result}")

            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.warning(f"Search intent analysis failed: {str(e)}")
            return {}

    async def _fetch_trends(self, keywords: List[str]) -> Dict[str, Any]:
        """Fetch seasonal search trends using PyTrends."""
        if not keywords:
            return {}

        try:
            self._pytrends.build_payload(keywords, timeframe="today 12-m")
            data = self._pytrends.interest_over_time()
            print(f"[KeywordAgent._fetch_trends] PyTrends data:\n{data.head() if not data.empty else 'Empty'}")

            if not data.empty:
                return data.drop("isPartial", axis=1, errors="ignore").to_dict()
            return {}
        except Exception as e:
            logger.warning(f"PyTrends fetch failed: {str(e)}")
            return {}

 