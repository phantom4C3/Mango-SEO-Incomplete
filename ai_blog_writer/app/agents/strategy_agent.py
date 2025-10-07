import logging
import json
from uuid import UUID
from typing import Dict, List, Any, Optional 

from ..clients.ai_clients import gemini_client 
from ..core.security import validate_language
from ..tools.google_search_tool import google_search_tool


logger = logging.getLogger(__name__)


class StrategyAgent:
    """
    Pre-Blog Strategy Agent - Combines competitor analysis, keyword research,
    search intent analysis, SEO analysis, and outline generation.
    """

    def __init__(self):
        self.clients = { 
            "gemini": gemini_client, 
        } 
        self.search_tool = google_search_tool

  

    async def generate_content_strategy(
        self,
        topic: str,
        target_keyword: str,
        task_id: UUID,   # convert str → UUID if needed
        url_id: UUID,    # convert str → UUID if needed
        competitors: Optional[List[str]] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive content strategy with minimal AI calls:
        - Call #1: _research_topic
        - Call #2: _generate_outline
        Optimized for Writing Agent consumption.
        """
        try:
            # Validate language
            if not validate_language(language):
                logger.warning(f"Unsupported language '{language}', defaulting to 'en'")
                language = "en"

            # --- AI Call #1: Research everything in one go ---
            try:
                research_data = await self._research_topic(
                    topic=topic,
                    target_keyword=target_keyword,
                    language=language,
                )
            except Exception as e:
                logger.error(f"Research topic failed: {str(e)}")
                research_data = self._generate_fallback_research(topic, target_keyword)

            enrich_with_search: bool = False,

             # Optional: Enrich competitors and gaps using search tool
            if enrich_with_search and self.search_tool:
                try:
                    search_competitors = await self.search_tool.find_competitors(target_keyword)
                    if search_competitors:
                        research_data["competitors"].extend(search_competitors)
                    
                    snippets = await self.search_tool.extract_snippets(target_keyword, num_results=5)
                    if snippets:
                        research_data["content_gaps"].extend(snippets)
                except Exception as e:
                    logger.warning(f"Search enrichment failed: {str(e)}")


            # Extract structured fields from research_data
            competitor_analysis = {"competitors": research_data.get("competitors", [])}
            keyword_research = research_data.get("semantic_keywords", [])
            content_gaps = research_data.get("content_gaps", [])
            common_questions = research_data.get("common_questions", [])
            search_intent = research_data.get("search_intent")
            if not search_intent:
                search_intent = self.detect_search_intent(target_keyword)

            
            # Create intent_analysis from search_intent
            intent_analysis = {
                "intent": search_intent,
                "confidence": 0.8 if research_data.get("search_intent") else 0.5,
                "method": "ai_research" if research_data.get("search_intent") else "rule_based"
                }

            # --- AI Call #2: Outline generation ---
            try:
                outline = await self._generate_outline(
                    research_data,
                    target_keyword,
                    language,
                    website_info=None,
                )
            except Exception as e:
                logger.warning(f"Outline generation failed: {str(e)}")
                outline = self._generate_fallback_outline(target_keyword, language)

            # Compile final strategy
            content_strategy = {
                "topic": topic,
                "target_keyword": target_keyword,
                "language": language,
                "search_intent": search_intent,
                "intent_analysis": intent_analysis,
                "competitor_analysis": competitor_analysis,
                "keyword_research": keyword_research,
                "seo_analysis": {},  # can be filled later if needed
                "research_data": research_data,
                "outline": outline,
                "competitors":topic.get("competitors", []),
                "semantic_keywords": keyword_research[:15],
                "content_gaps": content_gaps,
                "common_questions": common_questions,
                "verified_facts": [],  # populated later during writing
            }

            return content_strategy

        except Exception as e:
            logger.error(f"Content strategy generation failed: {str(e)}")
            return self._generate_fallback_strategy(topic, target_keyword, language)

    async def _research_topic(
        self, topic: str, target_keyword: str, language: str
    ) -> Dict[str, Any]:
        """Research the topic and generate comprehensive data."""
        try:
            prompt = f"""
            As a professional SEO researcher, analyze the topic "{topic}" with target keyword "{target_keyword}".
            Language: {language}

            Provide a comprehensive research report including:

            1. Top 5 competitor analysis with their strengths and weaknesses
            2. Common questions people ask about this topic
            3. Semantic keywords and related terms
            4. Content gaps and opportunities
            5. Search intent analysis

            Format your response as JSON:
            {{
              "competitors": [
                {{
                  "name": "Competitor Name",
                  "url": "competitor-url.com",
                  "strengths": ["strength1", "strength2"],
                  "weaknesses": ["weakness1", "weakness2"]
                }}
              ],
              "common_questions": ["question1", "question2"],
              "semantic_keywords": ["keyword1", "keyword2"],
              "content_gaps": ["gap1", "gap2"],
              "search_intent": "informational/commercial/transactional"
            }}
            """

            response = await gemini_client.generate_structured(prompt=prompt)

            if not response:
                return self._generate_fallback_research(topic, target_keyword)
 
            return response

        except Exception as e:
            logger.error(f"Topic research failed: {str(e)}")
            return self._generate_fallback_research(topic, target_keyword)

    async def _generate_outline(
        self,
        research_data: Dict,
        target_keyword: str,
        language: str,
        website_info: Optional[Dict] = None,
    ) -> Dict:
        """Generate article outline based on research data."""
        try:
            prompt = f"""
            Create a comprehensive article outline for target keyword "{target_keyword}".

            Competitor analysis: {json.dumps(research_data.get("competitors", []))}
            Common questions: {json.dumps(research_data.get("common_questions", []))}
            Semantic keywords: {json.dumps(research_data.get("semantic_keywords", []))}
            Search intent: {research_data.get("search_intent", "informational")}
            Language: {language}

            Important: The article outline should contain **exactly 7 sections** (H2 headings). 
            Distribute the content logically to cover all important subtopics.

            Structure required:
            1. Title
            2. SEO meta description
            3. Word count target
            4. Detailed structure with H2/H3 headings, keywords, and estimated length

            Format as JSON:
            {{
            "title": "Article Title",
            "meta_description": "SEO meta description",
            "word_count_target": 3000,
            "structure": [
                {{
                "heading": "H2 Heading",
                "subheadings": ["H3 Subheading 1", "H3 Subheading 2"],
                "keywords": ["keyword1", "keyword2"],
                "estimated_length": 500
                }}
            ]
            }}
            """


            outline_data = await gemini_client.generate_structured(prompt=prompt)

            if not outline_data:
                return self._generate_fallback_outline(target_keyword, language)
 
            outline_dict = outline_data
            outline_dict["language"] = language
            return outline_dict

        except Exception as e:
            logger.error(f"Outline generation failed: {str(e)}")
            return self._generate_fallback_outline(target_keyword, language)

    def _generate_fallback_research(
        self, topic: str, target_keyword: str
    ) -> Dict[str, Any]:
        """Generate fallback research data when AI fails."""
        return {
            "competitors": [
                {
                    "name": "Wikipedia",
                    "url": "wikipedia.org",
                    "strengths": ["Comprehensive", "Authoritative"],
                    "weaknesses": ["Not specialized", "Generic content"],
                },
                {
                    "name": "Industry Blog",
                    "url": "example.com/blog",
                    "strengths": ["Specialized", "Current"],
                    "weaknesses": ["Biased", "Limited scope"],
                },
            ],
            "common_questions": [
                f"What is {topic}?",
                f"How does {topic} work?",
                f"What are the benefits of {topic}?",
                f"How to get started with {topic}?",
            ],
            "semantic_keywords": [
                target_keyword,
                f"best {target_keyword}",
                f"{target_keyword} guide",
                f"how to use {target_keyword}",
            ],
            "content_gaps": [
                "Practical examples",
                "Step-by-step tutorials",
                "Case studies",
                "Video content",
            ],
            "search_intent": "informational",
        }

    def _generate_fallback_outline(self, target_keyword: str, language: str) -> Dict:
        """Generate fallback outline when AI fails (7 sections)."""
        return {
            "title": f"Comprehensive Guide to {target_keyword}",
            "meta_description": f"Learn everything about {target_keyword} with this comprehensive guide.",
            "word_count_target": 3000,
            "structure": [
                {
                    "heading": f"What is {target_keyword}?",
                    "subheadings": ["Definition", "Key Concepts", "Importance"],
                    "keywords": [target_keyword, f"what is {target_keyword}"],
                    "estimated_length": 400,
                },
                {
                    "heading": f"History / Background",
                    "subheadings": ["Origin", "Evolution", "Milestones"],
                    "keywords": [f"{target_keyword} history", f"{target_keyword} evolution"],
                    "estimated_length": 350,
                },
                {
                    "heading": f"Benefits of {target_keyword}",
                    "subheadings": ["Advantage 1", "Advantage 2", "Real-world Applications"],
                    "keywords": [f"benefits of {target_keyword}", f"{target_keyword} advantages"],
                    "estimated_length": 400,
                },
                {
                    "heading": "Implementation / How to Get Started",
                    "subheadings": ["Step-by-Step Guide", "Best Practices", "Common Mistakes to Avoid"],
                    "keywords": [f"how to use {target_keyword}", f"{target_keyword} tutorial"],
                    "estimated_length": 450,
                },
                {
                    "heading": "Case Studies / Examples",
                    "subheadings": ["Example 1", "Example 2", "Lessons Learned"],
                    "keywords": [f"{target_keyword} examples", f"{target_keyword} case studies"],
                    "estimated_length": 400,
                },
                {
                    "heading": "Advanced Tips / Strategies",
                    "subheadings": ["Tip 1", "Tip 2", "Pro Advice"],
                    "keywords": [f"{target_keyword} advanced", f"{target_keyword} strategies"],
                    "estimated_length": 400,
                },
                {
                    "heading": "Conclusion",
                    "subheadings": ["Summary", "Next Steps", "Additional Resources"],
                    "keywords": [f"{target_keyword} summary", f"{target_keyword} conclusion"],
                    "estimated_length": 300,
                },
            ],
            "language": language,
        }


    def _generate_fallback_strategy(
        self, topic: str, target_keyword: str, language: str
    ) -> Dict[str, Any]:
        """Generate fallback content strategy when all else fails."""
        fallback_research = self._generate_fallback_research(topic, target_keyword)
        return {
            "topic": topic,
            "target_keyword": target_keyword,
            "language": language,
            "search_intent": "informational",
            "intent_analysis": {
                "intent": "informational",
                "confidence": 0.5,
                "method": "fallback"
            },
            "competitor_analysis": {"competitors": fallback_research.get("competitors", [])},
            "keyword_research": fallback_research.get("semantic_keywords", []),
            "seo_analysis": {},
            "research_data": fallback_research,
            "outline": self._generate_fallback_outline(target_keyword, language),
            "content_gaps": fallback_research.get("content_gaps", []),
            "semantic_keywords": fallback_research.get("semantic_keywords", [])[:15],
            "common_questions": fallback_research.get("common_questions", []),
            "verified_facts": [],
            "status": "fallback_generated",
        }
        
        
    def detect_search_intent(self, target_keyword: str) -> str:
        keyword = target_keyword.lower()
        if any(x in keyword for x in ["buy", "purchase", "order"]):
            return "transactional"
        elif any(x in keyword for x in ["best", "top", "reviews"]):
            return "commercial"
        elif any(x in keyword for x in ["what is", "how to", "guide"]):
            return "informational"
        else:
            return "informational"  # default
