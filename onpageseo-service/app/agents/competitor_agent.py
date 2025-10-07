# onpageseo-service/app/agents/competitor_agent.py
import logging
import json
import asyncio 
from typing import Dict, List, Any
from urllib.parse import urlparse
import time

from ..clients.ai_clients import gemini_client
from ..core.config import get_settings
from shared_models.models import (
    AgentResult,
    AgentType,
)
from ..clients.api_clients import api_clients

settings = get_settings()
logger = logging.getLogger(__name__)


class CompetitorAgent:
    """
    Competitor Analysis Agent using SerpAPI + AI (No Ahrefs)
    Uses SerpAPI for data collection, AI for gap analysis only. 
    Does not generate recommendations directly – recommender handles that.
    """

    def __init__(self): 
        self.agent_type = AgentType.COMPETITOR
        self.ai_client = gemini_client

    async def analyze_competitors(
    self,
    url: str,
    industry: str,
    target_keywords: List[str],
    depth: str = "comprehensive",
) -> AgentResult:
        """
        Complete competitor analysis using SerpAPI data + AI analysis.
        Returns standardized AgentResult with raw competitor data only.
        """
        try:
            domain = urlparse(url).netloc
            start_time = time.time()

            # Get competitors
            competitors = await self._discover_competitors_serpapi(domain, target_keywords, industry)
            if not competitors:
                logger.warning("No competitors found via SerpAPI, using AI fallback")
                competitors = await self._discover_competitors_ai(domain, industry)

            # Analyze top competitors
            competitor_analyses = []
            for competitor in competitors[:5]:
                analysis = await self._analyze_competitor_with_serpapi(competitor, target_keywords)
                competitor_analyses.append(analysis)

            # Identify gaps
            gap_analysis = await self._identify_gaps(url, competitor_analyses, target_keywords)

            execution_time = time.time() - start_time

            return AgentResult(
                agent_type=AgentType.COMPETITOR,
                input_data={"url": url, "industry": industry, "keywords": target_keywords},
                output_data={
                    "competitors": competitor_analyses,
                    "gap_analysis": gap_analysis,
                    "competitive_landscape": {
                        "total_competitors": len(competitors),
                        "top_competitors_analyzed": len(competitor_analyses),
                        "analysis_depth": depth,
                    },
                    "metadata": {
                        "data_source": "serpapi",
                        "execution_time": round(execution_time, 2),
                        "analysis_timestamp": time.time(),
                        "target_keywords": target_keywords,
                        "industry": industry,
                    },
                },
                processing_time=execution_time,
                confidence_score=0.95,
                cost_estimate=0,
                tokens_used=0,
            )

        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return self._generate_fallback_analysis(url, industry, target_keywords)


    async def _discover_competitors_serpapi(
        self, domain: str, keywords: List[str], industry: str
    ) -> List[Dict]:
        """Discover competitors using SerpAPI organic results (no AI) with enrichment"""
        competitors = []

    # In competitor_agent.py - fix how you access the client
    async def _discover_competitors_serpapi(self, domain: str, keywords: List[str], industry: str) -> List[Dict]:
        competitors = []
        
         # Check if SerpAPI is configured
        if "serp" not in api_clients or not api_clients["serp"].api_key:
            logger.warning("SerpAPI not available - skipping API-based competitor discovery")
            return await self._discover_competitors_ai(domain, industry)  # Fallback to AI
    
        # Check if SerpAPI client is available and has API key
        serp_client = api_clients.get("serp")
        if not serp_client or not hasattr(serp_client, 'api_key') or not serp_client.api_key:
            logger.warning("SerpAPI not configured, skipping competitor discovery")
            return []
        
        try:
            for keyword in keywords[:3]:
                try:
                    # ✅ CORRECT: Use dictionary access
                    search_results = await api_clients["serp"].get_keyword_ranks(query=keyword)
                
                    if search_results and "organic_results" in search_results:
                        for result in search_results["organic_results"][
                            :10
                        ]:  # Top 10 results
                            competitor_url = result.get("link")
                            if competitor_url and domain not in competitor_url:
                                competitor_domain = urlparse(competitor_url).netloc

                                # Check if we already have this competitor
                                if not any(
                                    c["domain"] == competitor_domain
                                    for c in competitors
                                ):
                                    # Enrichment: get indexed pages and related searches
                                    indexed_pages = 0
                                    related_searches = []
                                    try:
                                        # site:domain search for indexing
                                        site_search = await api_clients["serp"].get_keyword_ranks(query=f"site:{competitor_domain}")

                                        if (
                                            site_search
                                            and "search_information" in site_search
                                        ):
                                            indexed_pages = site_search[
                                                "search_information"
                                            ].get("total_results", 0)

                                        # related searches for content ideas
                                        related_search = await api_clients["serp"].get_keyword_ranks(query=competitor_domain) 
                                        if (
                                            related_search
                                            and "related_searches" in related_search
                                        ):
                                            related_searches = [
                                                rs.get("query")
                                                for rs in related_search[
                                                    "related_searches"
                                                ][:5]
                                            ]
                                    except Exception as e:
                                        logger.warning(
                                            f"Failed to enrich competitor {competitor_domain}: {str(e)}"
                                        )

                                    competitors.append(
                                        {
                                            "name": result.get("title", "").split(
                                                " - "
                                            )[0][:100],
                                            "url": competitor_url,
                                            "domain": competitor_domain,
                                            "position": result.get("position"),
                                            "snippet": result.get("snippet", "")[:200],
                                            "source": "serpapi",
                                            "keyword": keyword,
                                            "serp_data": {
                                                "first_seen": time.time(),
                                                "search_volume": "unknown",  # Placeholder
                                                "indexed_pages": indexed_pages,
                                                "related_searches": related_searches,
                                            },
                                        }
                                    )
                        await asyncio.sleep(1)  # Rate limiting
                except Exception as e:
                    logger.warning(
                        f"SerpAPI search failed for keyword {keyword}: {str(e)}"
                    )
                    continue

            return competitors

        except Exception as e:
            logger.error(f"SerpAPI competitor discovery failed: {str(e)}")
            return [] 

    async def _discover_competitors_ai(self, domain: str, industry: str) -> List[Dict]:
        """Fallback AI-based competitor discovery (only when SerpAPI fails). Safe handling of invalid responses."""
        try:
            prompt = f"""
            Discover 5-8 main competitors for domain: {domain}
            Industry: {industry}

            Return ONLY JSON list with: name, url, domain, competitive_level
            Example: [{{"name": "Competitor1", "url": "https://competitor1.com", "domain": "competitor1.com", "competitive_level": "high"}}]
            """

            response = await self.ai_client.generate_structured(prompt=prompt)

            # 🔥 Fix: normalize Gemini response
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except Exception as e:
                    logger.warning(f"Failed to parse AI competitor response as JSON: {str(e)}")
                    response = []


            # Handle both list and dict formats
            if isinstance(response, list):
                competitors = response
            elif isinstance(response, dict) and "competitors" in response:
                competitors = response.get("competitors", [])
            else:
                competitors = []

            # Validate items
            safe_competitors = []
            for comp in competitors:
                if isinstance(comp, dict) and comp.get("domain"):
                    safe_competitors.append(
                        {
                            "name": comp.get("name", comp["domain"]),
                            "url": comp.get("url", f"https://{comp['domain']}"),
                            "domain": comp["domain"],
                            "competitive_level": comp.get(
                                "competitive_level", "unknown"
                            ),
                            "source": "ai_fallback",
                        }
                    )

            return safe_competitors

        except Exception as e:
            logger.error(f"AI competitor discovery failed: {str(e)}")
            return []

    async def _analyze_competitor_with_serpapi(
        self, competitor: Dict, target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Analyze competitor using SerpAPI data (minimal AI)"""
        try:

            # Use AI only for strategic analysis, not basic data collection
            prompt = f"""
            Analyze competitor based on SERP data:
            Competitor: {competitor['name']} ({competitor['domain']})
            SERP Position: {competitor.get('position', 'N/A')}
            Snippet: {competitor.get('snippet', 'No snippet available')}
            Target Keywords: {target_keywords}
            
            Provide brief analysis focusing on:
            1. SEO strength (0-100 score based on SERP presence)
            2. Content strategy (based on snippet and domain)
            3. Potential weaknesses
            
            Return JSON with: seo_score, content_strategy, weaknesses, opportunities
            """

            response = await self.ai_client.generate_structured(prompt=prompt)

            # 🔥 Fix: normalize Gemini response
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except Exception as e:
                    logger.warning(f"Failed to parse AI competitor response as JSON: {str(e)}")
                    response = []


            return {
                **competitor,
                **response, 
                "analysis_type": "serpapi_ai_hybrid",
                "analysis_timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Competitor analysis failed: {str(e)}")
            return {**competitor, "analysis_failed": True, "error": str(e)}

    async def _identify_gaps(
        self, url: str, competitor_analyses: List[Dict], target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Identify gaps using AI analysis (bulletproof version)."""
        try:
            competitor_summary = []
            for comp in competitor_analyses:
                if not comp.get("analysis_failed"):
                    competitor_summary.append(
                        {
                            "name": comp.get("name"),
                            "domain": comp.get("domain"),
                            "seo_score": comp.get("seo_score", 0),
                            "content_strategy": comp.get("content_strategy", ""),
                        }
                    )

            if not competitor_summary:
                logger.warning("No valid competitor analyses, returning fallback gaps")
                return {
                    "content_gaps": ["Lack of competitor data, recommend manual audit"],
                    "technical_opportunities": [],
                    "quick_wins": [],
                    "long_term_opportunities": [],
                    "analysis_failed": True,
                }

            prompt = f"""
            Identify SEO and content gaps for: {url}
            Based on analysis of {len(competitor_summary)} competitors: {json.dumps(competitor_summary, indent=2)[:1000]}
            Target Keywords: {target_keywords}

            Analyze and provide:
            1. Content gaps (missing topics or content types)
            2. Technical SEO opportunities
            3. Quick wins (easy to implement)
            4. Long-term opportunities

            Return JSON with: content_gaps, technical_opportunities, quick_wins, long_term_opportunities
            """

            response = await self.ai_client.generate_structured(prompt=prompt)

            # 🔥 Fix: normalize Gemini response
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except Exception as e:
                    logger.warning(f"Failed to parse AI gap analysis response: {str(e)}")
                    response = {}


            # Validate AI response
            if not isinstance(response, dict):
                logger.warning("Invalid AI gap analysis response, returning fallback")
                return {"analysis_failed": True}

            return {
                "content_gaps": response.get("content_gaps", []),
                "technical_opportunities": response.get("technical_opportunities", []),
                "quick_wins": response.get("quick_wins", []),
                "long_term_opportunities": response.get("long_term_opportunities", []),
            }

        except Exception as e:
            logger.error(f"Gap analysis failed: {str(e)}")
            return {"analysis_failed": True}


    def _generate_fallback_analysis(
    self, url: str, industry: str, keywords: List[str]
    ) -> AgentResult:
        """Generate fallback analysis wrapped in AgentResult"""
        domain = urlparse(url).netloc
        output_data = {
            "competitors": [
                {
                    "name": f"Sample Competitor in {industry}",
                    "url": "https://example-competitor.com",
                    "domain": "example-competitor.com",
                    "seo_score": 70,
                    "analysis_type": "fallback",
                }
            ],
            "gap_analysis": {
                "content_gaps": [
                    f"Create content about {keywords[0] if keywords else 'industry topics'}",
                    "Develop case studies and testimonials",
                ],
                "quick_wins": [
                    "Optimize page titles and meta descriptions",
                    "Improve internal linking structure",
                ],
            },
            "competitive_landscape": {
                "total_competitors": 1,
                "analysis_depth": "fallback",
            },
            "metadata": {"data_source": "fallback", "analysis_timestamp": time.time()},
        }

        return AgentResult(
            agent_type=AgentType.COMPETITOR,
            input_data={"url": url, "industry": industry, "keywords": keywords},
            output_data=output_data,
            processing_time=0,
            confidence_score=0.5,
            cost_estimate=0,
            tokens_used=0,
            error="Fallback competitor analysis used",
        )

 
 
 