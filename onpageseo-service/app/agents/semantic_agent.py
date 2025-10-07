from typing import Dict, List, Optional
import logging
import asyncio
from shared_models.models import AgentType, AgentResult
from ..clients.ai_clients import gemini_client
import json

logger = logging.getLogger(__name__)


class SemanticAgent:
    """AI agent for semantic content optimization and rewriting"""

    def __init__(self): 
        self.agent_type = AgentType.SEMANTIC
        self.ai_client = gemini_client  # use shared Gemini client

    async def optimize_content(
    self,
    content_type: str,
    original_content: str,
    context: Optional[Dict] = None,
    keywords: Optional[List[str]] = None,
    analyzer_context: Optional[Dict] = None,
) -> AgentResult:
        """
        Optimize content semantically for better SEO, readability, and E-E-A-T.
        Acts as orchestrator that calls other helpers and aggregates results.
        """
        try:
            # --- Step 1: Semantic optimization prompt ---
            if analyzer_context:
                content_issues = [
                    issue for issue in analyzer_context.get("issues", [])
                    if content_type in issue.get("type", "")
                ]
                enhanced_context = {**(context or {}), "analyzer_issues": content_issues}
                prompt = self._build_optimization_prompt(
                    content_type, original_content, enhanced_context, keywords
                )
            else:
                prompt = self._build_optimization_prompt(
                    content_type, original_content, context, keywords
                )

            response = await self.ai_client.generate_structured(
                prompt=prompt,  
            )

            optimization_data = self._parse_optimization_response(response, content_type)

            # --- Step 2: E-E-A-T optimization ---
            eeat_data = await self.optimize_for_eeat(
                content=original_content,
                author_credentials=context.get("author_credentials", {}) if context else {}
            )

            # --- Step 3: Aggregate results ---
            final_output = {
                "optimization": optimization_data,
                "eeat": eeat_data,
            }

            return AgentResult(
                agent_type=self.agent_type,
                input_data={
                    "content_type": content_type,
                    "content_length": len(original_content),
                    "keywords": keywords,
                    "analyzer_issues_count": (
                        len(analyzer_context.get("issues", []))
                        if analyzer_context else 0
                    ),
                },
                output_data=final_output,
                processing_time=response.get("processing_time", 0),
                confidence_score=response.get("confidence", 0.8),
                cost_estimate=response.get("cost_estimate", 0.05),  # combined
                tokens_used=response.get("tokens_used"),
            )

        except Exception as e:
            logger.error(f"Semantic optimization failed: {str(e)}")
            return AgentResult(
                agent_type=self.agent_type,
                input_data={
                    "content_type": content_type,
                    "content_length": len(original_content),
                    "keywords": keywords,
                    "analyzer_issues_count": (
                        len(analyzer_context.get("issues", []))
                        if analyzer_context else 0
                    ),
                },
                output_data={},
                processing_time=0,
                confidence_score=0.0,
                cost_estimate=0,
                tokens_used=0,
                error=str(e),
            )
 
    def _build_optimization_prompt(
        self,
        content_type: str,
        content: str,
        context: Optional[Dict],
        keywords: Optional[List[str]],
    ) -> str:
        """Build prompt for semantic optimization"""
        prompt_templates = {
            "title": """
            Optimize this page title for SEO and click-through rate:
            Original: {content}
            
            {context_section}
            Provide 3 improved versions with explanations.
            Consider: length (50-60 chars), keyword inclusion, emotional appeal.
            """,
            "meta_description": """
            Optimize this meta description for SEO and engagement:
            Original: {content}
            
            {context_section}
            Provide 3 improved versions (150-160 chars).
            Include: primary keyword, call-to-action, value proposition.
            """,
            "heading": """
            Optimize this heading for SEO and readability:
            Original: {content}
            
            {context_section}
            Provide 3 improved versions.
            Consider: hierarchy level, keyword placement, user intent.
            """,
            "content": """
            Optimize this content paragraph for SEO and readability:
            Original: {content}
            
            {context_section}
            Provide an improved version focusing on:
            - Keyword integration (natural placement)
            - Readability (shorter sentences, active voice)
            - Value to reader
            - Semantic richness
            """,
        }

        template = prompt_templates.get(content_type, prompt_templates["content"])

        # Build context section
        context_section = ""
        if context and context.get("analyzer_issues"):
            issues_text = "\n".join(
                [
                    f"- {issue.get('message')}"
                    for issue in context.get("analyzer_issues", [])
                ]
            )
            context_section = f"Current issues to address:\n{issues_text}\n\n"

        base_prompt = template.format(content=content, context_section=context_section)

        # Add keywords if provided
        if keywords:
            base_prompt += f"\nKeywords to include: {', '.join(keywords[:5])}"

        return base_prompt

    def _parse_optimization_response(self, response: Dict, content_type: str) -> Dict:
        """Parse AI response for content optimization"""
        try:
            return {
                "original": response.get("original", ""),
                "suggestions": response.get("suggestions", []),
                "improvement_areas": response.get("improvement_areas", []),
                "confidence_scores": response.get("confidence_scores", {}),
                "content_type": content_type,
            }
        except Exception as e:
            logger.error(f"Failed to parse optimization response: {str(e)}")
            return {
                "original": "",
                "suggestions": [],
                "improvement_areas": [],
                "confidence_scores": {},
                "content_type": content_type,
            }

    async def optimize_for_eeat(self, content: str, author_credentials: Dict) -> Dict:
        """Optimize content for Google's E-E-A-T guidelines"""
        prompt = f"""
        Optimize content for Experience, Expertise, Authoritativeness, Trustworthiness:
        Content: {content[:2000]}
        Author Credentials: {json.dumps(author_credentials)}
        
        Provide:
        1. E-E-A-T score assessment (0-100)
        2. Specific improvements for each E-E-A-T component
        3. Authority-building content suggestions
        4. Trust signals to add
        5. Citation and reference improvements
        
        Return JSON with: eeat_score, experience_improvements, 
        expertise_enhancements, authority_builders, trust_signals
        """
        
        response = await self.ai_client.generate_structured(
            prompt=prompt, 
        )
        return response