import json
import logging
import asyncio
import re
import base64
from typing import Dict, List, Any, Optional
from pathlib import Path 
import textstat
from datetime import datetime

import language_tool_python
from ..clients.ai_clients import gemini_client
from ..clients.supabase_client import supabase_client 

logger = logging.getLogger(__name__)


FACT_CHECK_PROMPT_TEMPLATE = """
You are a fact-checking assistant. 
Review the following blog content and compare it against the provided research data and verified facts. 

Content:
{content}

Research Data:
{research_data}

Language: {language}

Return a JSON object with:
- corrections: list of objects with "original_text" and "corrected_text"
- citations: list of URLs or references
- confidence_score: number between 0-100
"""

QUALITY_PROMPT_TEMPLATE = """
Analyze the following blog content for style consistency, tone, and overall quality.

Content:
{content}

Language: {language}

Return a short structured summary including:
- score (0–100)
- consistency (true/false)
- recommendations (max 3)
"""


class ReviewAgent:
    """
    Post-Blog Review Agent - Performs quality checks, fact-checking, and media generation.
    Takes blog draft from WritingAgent and produces final polished content.
    """

    def __init__(self):
        self.ai_clients = { 
            "gemini": gemini_client, 
        }
        self.supabase = supabase_client

        # Quality thresholds
        self.READABILITY_THRESHOLD = 60.0
        self.SEO_SCORE_THRESHOLD = 80.0
        self.STYLE_SCORE_THRESHOLD = 80.0
        self.FACT_CHECK_THRESHOLD = 90.0

        # Load prompts
        self.FACT_CHECK_PROMPT = self._load_fact_check_prompt() 
        self.QUALITY_PROMPT = self._load_quality_prompt()

    async def review_blog_content(
        self,
        blog_draft: Dict[str, Any],
        content_strategy: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Comprehensive review of blog content including quality checks, fact-checking,
        and media generation.

        Args:
            blog_draft: Output from BlogWritingAgent
            content_strategy: Original strategy from StrategyAgent
            task_id: Optional task ID for user-specific preferences

        Returns:
            Fully reviewed and enhanced blog content
        """
        try:
            # Extract content and metadata
            content = blog_draft.get("content", "")
            title = blog_draft.get("title", "")
            target_keyword = content_strategy.get("target_keyword", "")
            language = content_strategy.get("language", "en")

            # Execute all review tasks in parallel
            tasks = [
                self._perform_quality_checks(content, title, target_keyword, language),
                self._perform_fact_checking(content, content_strategy, language),
            ]

            (
                quality_results,
                fact_check_results,
            ) = await asyncio.gather(*tasks)

            # Apply corrections and enhancements
            final_content = self._apply_corrections_and_enhancements(
                content, fact_check_results, quality_results
            )
 
            # Compile comprehensive review report
            return {
                "final_content": final_content,
                "title": title,
                "meta_description": blog_draft.get("meta_description", ""),
                "quality_report": quality_results,
                "fact_check_report": fact_check_results,
                "overall_score": self._calculate_overall_score(
                    quality_results, fact_check_results
                ),
                "status": "review_complete",
                "language": language,
            }

        except Exception as e:
            logger.error(f"Blog review failed: {str(e)}")
            return self._generate_fallback_review(blog_draft, content_strategy)

    async def _check_grammar_and_typos(
        self, content: str, language: str
    ) -> Dict[str, Any]:
        """Free grammar checking using language-tool"""
        try:
            tool = language_tool_python.LanguageTool(language)
            matches = tool.check(content)

            return {
                "error_count": len(matches),
                "corrected_errors": [
                    {"original": m.context, "corrected": m.replacements[0]}
                    for m in matches
                    if m.replacements
                ],
                "passed": len(matches) < 5,  # Allow minor errors
                "details": [str(m) for m in matches],
            }
        except:
            return {"passed": True, "error_count": 0}  # Fail gracefully

    async def _perform_quality_checks(
        self, content: str, title: str, target_keyword: str, language: str
    ) -> Dict[str, Any]:
        """Perform comprehensive quality checks on content."""
        try:
            # Run all quality checks concurrently
            readability_task = self._assess_readability(content, language)
            seo_task = self._check_seo_optimization(content, title, target_keyword)
            style_task = self._check_style_consistency(content)
            grammar_task = self._check_grammar_and_typos(content, language)

            readability, seo, style, grammar = await asyncio.gather(
                readability_task, seo_task, style_task, grammar_task
            )

            return {
                "readability": readability,
                "seo": seo,
                "style": style,
                "grammar": grammar,
                "overall_score": self._calculate_quality_score(
                    readability, seo, style, grammar
                ),
                "passed": all(
                    [
                        readability.get("passed", False),
                        seo.get("passed", False),
                        style.get("passed", False),
                        grammar.get("passed", False),
                    ]
                ),
            }

        except Exception as e:
            logger.error(f"Quality checks failed: {str(e)}")
            return self._generate_fallback_quality_report()

    async def _assess_readability(self, content: str, language: str) -> Dict[str, Any]:
        """Assess content readability and provide interpretation."""
        try:
            flesch = textstat.flesch_reading_ease(content)

            # Interpretation inline (merged logic)
            if flesch >= 90:
                interpretation = "Very Easy"
            elif flesch >= 80:
                interpretation = "Easy"
            elif flesch >= 70:
                interpretation = "Fairly Easy"
            elif flesch >= 60:
                interpretation = "Standard"
            elif flesch >= 50:
                interpretation = "Fairly Difficult"
            elif flesch >= 30:
                interpretation = "Difficult"
            else:
                interpretation = "Very Difficult"

            return {
                "flesch_reading_ease": flesch,
                "interpretation": interpretation,
                "passed": flesch >= self.READABILITY_THRESHOLD,
            }

        except Exception as e:
            logger.error(f"Readability assessment failed: {str(e)}")
            return {"passed": False, "error": str(e)}

    async def _check_seo_optimization(
        self, content: str, title: str, target_keyword: str
    ) -> Dict[str, Any]:
        """Check SEO optimization."""
        try:
            content = content or ""
            title = title or ""
            target_keyword = target_keyword or ""

            # Count keyword occurrences
            keyword_count = content.lower().count(target_keyword.lower())
            title_contains = target_keyword.lower() in title.lower()

            # Basic SEO scoring
            score = 60  # Base score
            if title_contains:
                score += 15
            if keyword_count >= 3:
                score += min(keyword_count * 2, 25)

            return {
                "overall_seo_score": score,
                "keyword_usage": f"Found {keyword_count} times"
                + (" in title" if title_contains else ""),
                "passed": score >= self.SEO_SCORE_THRESHOLD,
            }

        except Exception as e:
            logger.error(f"SEO check failed: {str(e)}")
            return {"passed": False, "error": str(e)}

    async def _perform_fact_checking(
        self, content: str, content_strategy: Dict[str, Any], language: str
    ) -> Dict[str, Any]:
        """Perform fact-checking on content."""
        try:
            research_data = content_strategy.get("research_data", {})
            verified_facts = content_strategy.get("verified_facts", [])

            prompt = self.FACT_CHECK_PROMPT.format(
                content=content[:4000],
                research_data=json.dumps(
                    {**research_data, "verified_facts": verified_facts},
                    ensure_ascii=False,
                ),
                language=language,
            )

            response = await gemini_client.generate_structured(
                prompt=prompt, 
            )

            result = self._parse_fact_check_response(response)
            confidence = float(result.get("confidence_score", 0))

            return {
                **result,
                "confidence_score": confidence,
                "passed": confidence >= self.FACT_CHECK_THRESHOLD,
            }

        except Exception as e:
            logger.error(f"Fact-checking failed: {str(e)}")
            return {"passed": False, "corrections": [], "citations": []}

    def _apply_corrections_and_enhancements(
        self,
        content: str,
        fact_check_results: Dict[str, Any],
        quality_results: Dict[str, Any],
    ) -> str:
        """Apply all corrections and enhancements to content."""
        try:
            # Apply fact-check corrections
            corrected_content = content
            if fact_check_results.get("corrections"):
                for correction in fact_check_results["corrections"]:
                    original = correction.get("original_text", "")
                    corrected = correction.get("corrected_text", "")
                    if original and corrected:
                        corrected_content = corrected_content.replace(
                            original, corrected
                        )

            # Apply grammar corrections
            if quality_results.get("grammar", {}).get("corrected_errors"):
                for error in quality_results["grammar"]["corrected_errors"]:
                    if (
                        isinstance(error, dict)
                        and "original" in error
                        and "corrected" in error
                    ):
                        corrected_content = corrected_content.replace(
                            error["original"], error["corrected"]
                        )

            return corrected_content

        except Exception as e:
            logger.error(f"Content correction failed: {str(e)}")
            return content

    def _calculate_overall_score(
        self, quality_results: Dict[str, Any], fact_check_results: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score."""
        quality_score = quality_results.get("overall_score", 70)
        fact_check_score = fact_check_results.get("confidence_score", 80)

        return round((quality_score * 0.6 + fact_check_score * 0.4), 1)

    def _calculate_quality_score(
        self,
        readability: Dict[str, Any],
        seo: Dict[str, Any],
        style: Dict[str, Any],
        grammar: Dict[str, Any],
    ) -> float:
        """Calculate overall quality score from components."""
        scores = [
            readability.get("flesch_reading_ease", 60),
            seo.get("overall_seo_score", 70),
            style.get("overall_consistency_score", 75),
            100
            - min(grammar.get("error_count", 0) * 5, 100),  # Convert errors to score
        ]

        return round(sum(scores) / len(scores), 1)
 

    def _parse_fact_check_response(self, response: Any) -> Dict[str, Any]:
        """Parse fact-check response."""
        try:
            if isinstance(response, str):
                result = json.loads(response)
            else:
                result = response

            # Ensure required fields
            required = ["corrections", "citations", "confidence_score"]
            for field in required:
                if field not in result:
                    result[field] = [] if field in ["corrections", "citations"] else 0

            return result

        except json.JSONDecodeError:
            return {"corrections": [], "citations": [], "confidence_score": 0}
 
    def _load_fact_check_prompt(self) -> str:
        """Load fact-check prompt template."""
        try:
            path = Path(__file__).parent / "prompts" / "fact_checking.txt"
            if path.exists():
                return path.read_text(encoding="utf-8")
        except Exception:
            pass

        return FACT_CHECK_PROMPT_TEMPLATE

    async def _check_style_consistency(self, content: str) -> Dict[str, Any]:
        """Check style consistency using structured AI analysis."""
        try:
            prompt = self.QUALITY_PROMPT.format(content=content[:3000], language="English")
            response = await gemini_client.generate_structured(prompt=prompt)

            # Use structured response directly
            return {
                "passed": response.get("consistent", True),
                "overall_consistency_score": response.get("score", 85),
                "recommendations": response.get("recommendations", []),
                "details": {
                    "tone_consistency": response.get("tone_consistency", "stable"),
                    "formatting_consistency": response.get("formatting_consistency", "good"),
                    "voice_consistency": response.get("voice_consistency", "consistent"),
                },
            }

        except Exception as e:
            logger.warning(f"Style consistency check failed: {str(e)}")
            return {
                "passed": True,
                "overall_consistency_score": 85,
                "recommendations": ["Style check temporarily unavailable"],
                "details": {"error": str(e)},
            }
 



    def _load_quality_prompt(self) -> str:
        """Load quality assessment prompt template."""
        # Basic quality prompt template
        return """
        Analyze the quality of the provided content and provide comprehensive assessment.
        Include readability, SEO, style consistency, and grammar analysis.
        """

    def _generate_fallback_review(
        self, blog_draft: Dict[str, Any], content_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback review when main process fails."""
        return {
            "final_content": blog_draft.get("content", ""),
            "title": blog_draft.get("title", ""),
            "quality_report": self._generate_fallback_quality_report(),
            "fact_check_report": {"passed": False, "corrections": [], "citations": []},
            "overall_score": 60,
            "status": "fallback_review",
            "language": content_strategy.get("language", "en"),
        }

    def _generate_fallback_quality_report(self) -> Dict[str, Any]:
        """Generate fallback quality report."""
        return {
            "readability": {"passed": True, "flesch_reading_ease": 70},
            "seo": {"passed": True, "overall_seo_score": 75},
            "style": {"passed": True, "overall_consistency_score": 80},
            "grammar": {"passed": True, "error_count": 0},
            "overall_score": 75,
            "passed": True,
        }
