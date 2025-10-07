import logging
import json
from typing import List, Dict, Any
from ..clients.ai_clients import  gemini_client
from pytrends.request import TrendReq

logger = logging.getLogger(__name__)

class TopicAgent:
    """Specialized agent for blog topic ideation and discovery"""
    
    def __init__(self):
        self.clients = { 
            "gemini": gemini_client,
        }
        # Pytrends instance
        self.pytrends = TrendReq(hl='en-US', tz=360)
    
    async def generate_blog_topics(
    self,
    website_url: str,
    title: str,
    description: str,
    count: int = 10,
    include_trends: bool = False
) -> List[Dict[str, Any]]:
        """
        Generate SEO-optimized blog topic ideas, ensures exactly `count` topics.
        """
        try:
            
            include_trends = True  # Auto-include trends if website info exists

            prompt = self._build_topic_generation_prompt(
                website_url, title, description, count
            )
            print("🔍 [TopicAgent] Prompt sent to Gemini:\n", prompt)

            response = await gemini_client.generate_structured(prompt=prompt)
            print("🔍 [TopicAgent] Raw Gemini response:\n", response)

                    
            # ✅ Fixed code
            topics_data = response
            if isinstance(topics_data, list):
                topics = topics_data
            elif isinstance(topics_data, dict):
                topics = topics_data.get("topics", [])
            else:
                topics = []
            print("🔍 [TopicAgent] Parsed topics:", topics)

            # Optional: Enhance with trends
            if include_trends:
                for topic in topics:
                    trending_keywords = self.get_trending_keywords(topic["title"], top_n=3)
                    if trending_keywords:
                        topic["title"] += f" ({', '.join(trending_keywords)})"
                        topic["meta_description"] += f" Trending keywords: {', '.join(trending_keywords)}"

            # 🔹 ENSURE EXACT COUNT
            if len(topics) > count:
                topics = topics[:count]
            elif len(topics) < count:
                fallback_topics = self._generate_fallback_topics(title, count - len(topics))
                topics.extend(fallback_topics)

            return topics

        except Exception as e:
            logger.error(f"Topic generation failed: {str(e)}")
            return self._generate_fallback_topics(title, count, include_trends)

    
    def _build_topic_generation_prompt(
        self,
        website_url: str,
        title: str,
        description: str,
        count: int,
        include_trends: bool = False
    ) -> str:
        trend_section = "Focus on currently trending topics in the industry.\n" if include_trends else ""
    
        return f"""
        Based on the website: {website_url}
        Title: {title}
        Description: {description}
        
        {trend_section}
        Generate {count} unique, SEO-optimized blog topic ideas.
        Return ONLY a JSON array of topic objects, each with:
        - title: The full headline
        - slug: URL-friendly version
        - meta_description: 150-160 character description
        - target_keyword: Primary keyword for SEO
        - content_angle: Type of content (guide, list, comparison, etc.)
        """
        
    def _generate_fallback_topics(self, title: str, count: int, include_trends: bool = False) -> List[Dict[str, Any]]:
        """Generate fallback topics when AI fails"""
        base_topics = [
            {
                "title": f"Ultimate Guide to {title}",
                "slug": f"ultimate-guide-{title.lower().replace(' ', '-')}",
                "meta_description": f"Complete guide to understanding and using {title}",
                "target_keyword": f"{title} guide",
                "content_angle": "guide"
            },
            {
                "title": f"Top 10 Benefits of {title}",
                "slug": f"top-10-benefits-{title.lower().replace(' ', '-')}",
                "meta_description": f"Discover the top benefits of using {title}",
                "target_keyword": f"{title} benefits",
                "content_angle": "listicle"
            }
        ]

        if include_trends:
            trending_keywords = self.get_trending_keywords(title, top_n=3)
            for kw in trending_keywords:
                base_topics.append({
                    "title": f"{title} Trends: {kw}",
                    "slug": f"{title.lower().replace(' ', '-')}-trend-{kw.lower().replace(' ', '-')}",
                    "meta_description": f"Explore the latest trend related to {title}: {kw}",
                    "target_keyword": kw,
                    "content_angle": "trend"
                })

        return base_topics[:count]
    
    def get_trending_keywords(self, topic: str, top_n: int = 5) -> List[str]:
        """Fetch trending keywords related to the topic from Google Trends"""
        try:
            self.pytrends.build_payload([topic], timeframe='now 7-d')
            
            trending = self.pytrends.related_queries().get(topic, {}).get('top', [])
            if trending is not None and isinstance(trending, dict) and 'query' in trending:
                return trending['query'].tolist()[:top_n]
            return []

            # return trending['query'].tolist()[:top_n] if trending is not None else []
        except Exception as e:
            logger.warning(f"Failed to fetch trending keywords for '{topic}': {e}")
            return []
