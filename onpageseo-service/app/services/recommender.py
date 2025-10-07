# onpageseo-service/app/services/recommender.py
from typing import Dict, List, Optional, Any
import json
import logging
import asyncio
from datetime import datetime
import uuid
from shared_models.models import (
    SEOAuditResult,
    AIRecommendation,
    AgentResult,
    AgentType, 
     PageSEOData,
    TaskStatus,
)
from ..agents.keyword_agent import KeywordAgent
from ..agents.semantic_agent import SemanticAgent
from ..agents.schema_agent import SchemaAgent
from ..agents.competitor_agent import CompetitorAgent
from ..agents.performance_agent import PerformanceAgent
from ..clients.supabase_client import supabase_client
from ..clients.redis_client import redis_client
from .analytics_helper import AnalyticsHelper

logger = logging.getLogger(__name__)

def serialize(obj):
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, (uuid.UUID,)):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class SEORecommender:
    """Service that orchestrates AI agents to generate SEO recommendations"""

    def __init__(self):
        self.keyword_agent = KeywordAgent()
        self.semantic_agent = SemanticAgent()
        self.schema_agent = SchemaAgent()
        self.competitor_agent = CompetitorAgent()
        self.performance_agent = PerformanceAgent()


    # Key fixes for recommender.py - apply these changes to your existing file

    async def generate_recommendations(
        self, audit_result: SEOAuditResult, task_id: Optional[str] = None
    ) -> List[AIRecommendation]:
        """
        Generate AI-powered recommendations based on audit results.
        Full logging enabled to track which agents ran and their outputs.
        Ensures page_seo_data row exists to prevent foreign key violations.
        """
        try:
            # Update task status to processing
            if task_id:
                await self._update_task_status(
                    task_id, TaskStatus.PROCESSING, "Generating SEO recommendations"
                )

            page_data = audit_result.page_data
            if not page_data:
                error_msg = f"No page content found for URL ID: {audit_result.url_id}"
                logger.error(error_msg)
                if task_id:
                    await self._update_task_status(task_id, TaskStatus.FAILED, error_msg)
                return []

            # ✅ Ensure URL ID is present and properly formatted
            page_data.url_id = audit_result.url_id
            url_id_str = str(page_data.id) if page_data.id else str(audit_result.url_id)

            # ✅ Prepare page row data with proper field mapping
            page_row = {
                "id": url_id_str,
                "task_id": task_id,  # ✅ Add task_id field
                "url": page_data.url,
                "content_text": page_data.content_text,
                "title": page_data.title,
                # ✅ Properly serialize complex objects
                "schema_markup": json.dumps([
                    s.__dict__ if hasattr(s, '__dict__') else s 
                    for s in page_data.schema_markup
                ]) if page_data.schema_markup else None,
                "content_metrics": json.dumps(
                    page_data.content_metrics.__dict__
                ) if page_data.content_metrics else None,
                "extracted_keywords": page_data.extracted_keywords or [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }

            try:
                # ✅ Ensure page_seo_data exists before running agents
                existing_page = await supabase_client.fetch_one(
                    "page_seo_data",
                    filters={"id": url_id_str}
                )

                if existing_page:
                    # Update existing row (do not overwrite created_at)
                    row_updates = page_row.copy()
                    row_updates.pop("created_at")
                    row_updates.pop("id")  # Don't update the ID
                    await supabase_client.update_table(
                        "page_seo_data",
                        filters={"id": url_id_str},
                        updates=row_updates,
                    )
                    logger.info(f"[Task {task_id}] Page updated in page_seo_data: {page_data.url}")
                else:
                    # Insert new row
                    await supabase_client.insert_into("page_seo_data", page_row)
                    logger.info(f"[Task {task_id}] Page inserted into page_seo_data: {page_data.url}")

            except Exception as e:
                error_msg = f"Could not persist page_seo_data: {str(e)}"
                logger.error(f"[Task {task_id}] {error_msg}")
                # ✅ Don't fail completely - continue without agent runs logging
                url_id_str = None  # This will prevent agent runs from being logged

            # ✅ Run all AI agents with proper error handling
            agent_results_list = await self._run_ai_agents(audit_result, page_data, task_id, url_id_str)

            # Log agent outputs
            for res in agent_results_list:
                logger.info(
                    f"[Task {task_id}] Agent {res.agent_type.value} completed. "
                    f"Confidence: {res.confidence_score}, Output: {json.dumps(res.output_data, default=serialize)}"
                )

            # Convert list -> dict for easy access
            agent_results = {res.agent_type: res for res in agent_results_list}

            # Record which agents actually produced output
            audit_result.ai_agents_used = [
                res.agent_type.value for res in agent_results_list if res.output_data
            ]
            logger.info(
                f"[Task {task_id}] AI agents used for URL {audit_result.url}: "
                f"{audit_result.ai_agents_used}"
            )

            # Convert agent outputs to recommendations
            recommendations = await self._convert_to_recommendations(agent_results, audit_result)

            # Prioritize recommendations
            prioritized_recommendations = self._prioritize_recommendations(recommendations)
            logger.info(f"[Task {task_id}] Total recommendations generated: {len(prioritized_recommendations)}")

            # Store recommendations in DB and cache
            if url_id_str:  # Only store if we have a valid URL ID
                await self._store_recommendations(url_id_str, prioritized_recommendations, task_id)

            # Update task status to completed
            if task_id:
                await self._update_task_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    f"Generated {len(prioritized_recommendations)} SEO recommendations",
                )

            return prioritized_recommendations

        except Exception as e:
            error_msg = f"Recommendation generation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if task_id:
                await self._update_task_status(task_id, TaskStatus.FAILED, error_msg)
            return []



    # ✅ Update the _update_task_status method to use correct table name
    async def _update_task_status(
        self, task_id: str, status: TaskStatus, message: str = ""
    ):
        """Update task status in database"""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.now().isoformat(),
            }

            if message:
                update_data["progress_message"] = message

            # If task is completed or failed, set completed_at
            if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                update_data["completed_at"] = datetime.now().isoformat()

            # ✅ Use correct table name
            await supabase_client.update_table("seo_tasks", {"id": task_id}, update_data)
            logger.info(f"Updated task {task_id} status to {status.value}")

        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")

    # ✅ Update the _run_ai_agents method signature
    async def _run_ai_agents(
        self,
        audit_result: SEOAuditResult,
        page_data: PageSEOData,
        task_id: Optional[str] = None,
        url_id_str: Optional[str] = None,  # ✅ Add this parameter
    ) -> List[AgentResult]:
        """Run AI agents with logging of retries, failures, and fallback usage"""

        extracted_keywords = page_data.extracted_keywords
        industry = audit_result.analyzer_context.get("industry") if audit_result.analyzer_context else None

        agent_tasks: Dict[AgentType, callable] = {
            AgentType.KEYWORD: lambda: self.keyword_agent.run(
                url=page_data.url,
                content=page_data.content_text,
                keywords=extracted_keywords,
            ),
            AgentType.COMPETITOR: lambda: self.competitor_agent.analyze_competitors(
                url=page_data.url,
                industry=industry,
                target_keywords=extracted_keywords,
                depth="comprehensive",
            ),
            AgentType.PERFORMANCE: lambda: self._run_performance_agent(page_data),
            AgentType.SEMANTIC: lambda: self.semantic_agent.optimize_content(
                content_type=self._determine_page_type(page_data),
                original_content=page_data.content_text,
                context={"metrics": page_data.content_metrics.__dict__ if page_data.content_metrics else {}},
                keywords=extracted_keywords,
                analyzer_context=audit_result.analyzer_context,
            ),
            AgentType.SCHEMA: lambda: self.schema_agent.generate_schema(
                content=page_data.content_text,
                page_type=self._determine_page_type(page_data),
                existing_schema=page_data.schema_markup,
                analyzer_context=audit_result.analyzer_context,
            ),
        }

        results: List[AgentResult] = []
        for agent_type, fn in agent_tasks.items():
            logger.info(f"[Task {task_id}] Starting agent: {agent_type.value}")
            result = await self._run_with_retries(
                agent_type, 
                task_id, 
                fn, 
                url_id=url_id_str  # ✅ Pass the string URL ID
            )
            
            if result.output_data:
                logger.info(f"[Task {task_id}] Agent {agent_type.value} returned output: {json.dumps(result.output_data, default=serialize)}")
            else:
                logger.warning(f"[Task {task_id}] Agent {agent_type.value} returned EMPTY output. Fallback used? {result.confidence_score == 0.0}")

            results.append(result)

        logger.info(f"[Task {task_id}] All AI agents completed. Agents executed: {[r.agent_type.value for r in results]}")
        return results



    # ✅ Update the _run_with_retries method
    async def _run_with_retries(
        self,
        agent_type: AgentType,
        task_id: str,
        task_fn: callable,
        url_id: Optional[str] = None,
        max_attempts: int = 3,
        backoff: int = 2,
    ) -> AgentResult:
        """Centralized retry logic for any agent"""
        attempt = 0
        result: Optional[AgentResult] = None

        while attempt < max_attempts:
            attempt += 1
            try:
                logger.info(f"[Task {task_id}] Running {agent_type} attempt {attempt}")
                result = await task_fn()

                # ✅ Only persist run if url_id is available (page_seo_data exists)
                if url_id:
                    try:
                        await supabase_client.insert_into(
                            "seo_agent_runs",
                            {
                                "task_id": task_id if task_id else None,
                                "agent_type": agent_type.value,
                                "attempt": attempt,
                                "status": "success",
                                "url_id": url_id,
                                "created_at": datetime.utcnow().isoformat(),
                            },
                        )
                    except Exception as db_error:
                        logger.warning(f"[Task {task_id}] Failed to log agent run: {str(db_error)}")
                        # Don't fail the agent execution due to logging issues

                logger.info(f"[Task {task_id}] {agent_type} succeeded on attempt {attempt}")
                break

            except Exception as e:
                logger.error(f"[Task {task_id}] {agent_type} attempt {attempt} failed: {str(e)}")

                # ✅ Only persist failure if url_id is available
                if url_id:
                    try:
                        await supabase_client.insert_into(
                            "seo_agent_runs",
                            {
                                "task_id": task_id if task_id else None,
                                "agent_type": agent_type.value,
                                "attempt": attempt,
                                "status": "failed",
                                "url_id": url_id,
                                "error_message": str(e),
                                "created_at": datetime.utcnow().isoformat(),
                            },
                        )
                    except Exception as db_error:
                        logger.warning(f"[Task {task_id}] Failed to log agent failure: {str(db_error)}")

                if attempt < max_attempts:
                    await asyncio.sleep(backoff**attempt)

        if not result:
            logger.warning(
                f"[Task {task_id}] {agent_type} failed after {max_attempts} attempts. Using fallback."
            )
            result = self._create_fallback_result(agent_type)

        return result

    async def _convert_to_recommendations(
        self, agent_results: Dict[AgentType, AgentResult], audit_result: SEOAuditResult
    ) -> List[AIRecommendation]:
        """
        Convert agent results into actionable AI recommendations.
        Deduplicates recommendations while ensuring all AI-reported issues are included.
        """
        all_recommendations = []

        # Keyword recommendations
        if AgentType.KEYWORD in agent_results:
            all_recommendations.extend(
                self._create_keyword_recommendations(agent_results[AgentType.KEYWORD], audit_result)
            )

        # Semantic recommendations
        if AgentType.SEMANTIC in agent_results:
            all_recommendations.extend(
                self._create_semantic_recommendations(agent_results[AgentType.SEMANTIC], audit_result)
            )

        # Schema recommendations
        if AgentType.SCHEMA in agent_results:
            all_recommendations.extend(
                self._create_schema_recommendations(agent_results[AgentType.SCHEMA], audit_result)
            )

        # Performance recommendations
        if AgentType.PERFORMANCE in agent_results:
            all_recommendations.extend(
                self._create_performance_recommendations(agent_results[AgentType.PERFORMANCE], audit_result)
            )

        # Competitor recommendations
        if AgentType.COMPETITOR in agent_results:
            all_recommendations.extend(
                self._create_competitor_recommendations(agent_results[AgentType.COMPETITOR], audit_result)
            )

        # Deduplicate recommendations by (type, suggested)
        seen = set()
        deduped_recommendations = []
        for rec in all_recommendations:
            key = (rec.type, rec.suggested)
            if key not in seen:
                deduped_recommendations.append(rec)
                seen.add(key)

        return deduped_recommendations
 

    def _create_keyword_recommendations(
        self, keyword_result: AgentResult, audit_result: SEOAuditResult
    ) -> List[AIRecommendation]:
        """Create recommendations from keyword analysis"""
        recommendations = []

        # Add primary keyword recommendation
        if keyword_result.output_data.get("primary_keyword"):
            recommendations.append(
                AIRecommendation(
                    type="primary_keyword_optimization",
                    original=(
                        audit_result.metrics.primary_keyword
                        if audit_result.metrics
                        else ""
                    ),
                    suggested=keyword_result.output_data["primary_keyword"],
                    confidence_score=keyword_result.confidence_score,
                    reasoning="Optimized primary keyword for better search relevance",
                    impact_score=0.9,
                    agent_type=AgentType.KEYWORD,
                    implementation_complexity="medium",
                    estimated_time=30,
                )
            )

        # Add keyword density recommendations
        if keyword_result.output_data.get("keyword_density_suggestions"):
            for suggestion in keyword_result.output_data["keyword_density_suggestions"][
                :3
            ]:
                recommendations.append(
                    AIRecommendation(
                        type="keyword_density_optimization",
                        original="",
                        suggested=suggestion,
                        confidence_score=0.7,
                        reasoning="Keyword density optimization opportunity",
                        impact_score=0.6,
                        agent_type=AgentType.KEYWORD,
                        implementation_complexity="low",
                        estimated_time=15,
                    )
                )

        # Add semantic keyword opportunities
        if keyword_result.output_data.get("semantic_keywords"):
            for keyword in keyword_result.output_data["semantic_keywords"][:5]:
                recommendations.append(
                    AIRecommendation(
                        type="semantic_keyword_addition",
                        original="",
                        suggested=keyword,
                        confidence_score=0.65,
                        reasoning="Semantic keyword to improve content relevance",
                        impact_score=0.5,
                        agent_type=AgentType.KEYWORD,
                        implementation_complexity="low",
                        estimated_time=10,
                    )
                )

        return recommendations

    def _create_semantic_recommendations(
        self, semantic_result: AgentResult, audit_result: SEOAuditResult
    ) -> List[AIRecommendation]:
        """Create recommendations from semantic analysis"""
        recommendations = []

        # Title optimization
        if semantic_result.output_data.get("optimized_title"):
            recommendations.append(
                AIRecommendation(
                    type="title_optimization",
                    original=audit_result.metrics.title if audit_result.metrics else "",
                    suggested=semantic_result.output_data["optimized_title"],
                    confidence_score=semantic_result.confidence_score,
                    reasoning="Semantically optimized title for better CTR and relevance",
                    impact_score=0.85,
                    agent_type=AgentType.SEMANTIC,
                    implementation_complexity="low",
                    estimated_time=5,
                )
            )

        # Meta description optimization
        if semantic_result.output_data.get("optimized_meta_description"):
            recommendations.append(
                AIRecommendation(
                    type="meta_description_optimization",
                    original=(
                        audit_result.metrics.meta_description
                        if audit_result.metrics
                        else ""
                    ),
                    suggested=semantic_result.output_data["optimized_meta_description"],
                    confidence_score=semantic_result.confidence_score
                    * 0.9,  # Slightly lower confidence_score for meta
                    reasoning="Improved meta description for higher click-through rates",
                    impact_score=0.7,
                    agent_type=AgentType.SEMANTIC,
                    implementation_complexity="low",
                    estimated_time=5,
                )
            )

        # Content optimization suggestions
        if semantic_result.output_data.get("content_suggestions"):
            for i, suggestion in enumerate(
                semantic_result.output_data["content_suggestions"][:3]
            ):
                recommendations.append(
                    AIRecommendation(
                        type="content_optimization",
                        original="",
                        suggested=suggestion,
                        confidence_score=0.7,
                        reasoning="Semantic content improvement for better engagement",
                        impact_score=0.6,
                        agent_type=AgentType.SEMANTIC,
                        implementation_complexity="medium",
                        estimated_time=25,
                    )
                )

        return recommendations

    def _create_schema_recommendations(
        self, schema_result: AgentResult, audit_result: SEOAuditResult
    ) -> List[AIRecommendation]:
        """Create recommendations from schema analysis"""
        recommendations = []

        if schema_result.output_data.get("schema_json"):
            schema_type = schema_result.output_data.get("schema_type", "Article")

            recommendations.append(
                AIRecommendation(
                    type="schema_markup",
                    original=(
                        "No structured data"
                        if not audit_result.issues
                        or not any(
                            issue.type == "missing_schema"
                            for issue in audit_result.issues
                        )
                        else "Incomplete structured data"
                    ),
                    suggested=json.dumps(
                        schema_result.output_data["schema_json"], indent=2, default=serialize
                    ),
                    confidence_score=schema_result.confidence_score,
                    reasoning=f"Add {schema_type} schema markup for rich results and better visibility",
                    impact_score=0.8,
                    agent_type=AgentType.SCHEMA,
                    implementation_complexity="high",
                    estimated_time=45,
                )
            )

        # Schema validation recommendations
        if schema_result.output_data.get("validation_issues"):
            for issue in schema_result.output_data["validation_issues"][:2]:
                recommendations.append(
                    AIRecommendation(
                        type="schema_validation",
                        original="",
                        suggested=issue.get("fix", ""),
                        confidence_score=0.8,
                        reasoning=f"Schema validation issue: {issue.get('message', '')}",
                        impact_score=0.4,
                        agent_type=AgentType.SCHEMA,
                        implementation_complexity="medium",
                        estimated_time=20,
                    )
                )

        return recommendations
    
    
    def _create_competitor_recommendations(
    self, competitor_result: AgentResult, audit_result: SEOAuditResult
) -> List[AIRecommendation]:
        """Convert CompetitorAgent output into actionable AI recommendations"""
        recommendations = []
        data = competitor_result.output_data or {}

        competitors = data.get("competitors", [])
        gap_analysis = data.get("gap_analysis", {})

        # 1️⃣ Recommendations based on individual competitor analysis
        for comp in competitors[:5]:  # limit to top 5 competitors
            name = comp.get("name", comp.get("domain", "Unknown Competitor"))
            seo_score = comp.get("seo_score", 0)
            content_strategy = comp.get("content_strategy", "")
            weaknesses = comp.get("weaknesses", [])
            opportunities = comp.get("opportunities", [])

            # Suggest improvements for low SEO score competitors
            if seo_score < 70:
                recommendations.append(
                    AIRecommendation(
                        type="competitor_seo_gap",
                        original=f"{name} SEO score: {seo_score}",
                        suggested="Improve on-page SEO and keyword targeting",
                        confidence_score=competitor_result.confidence_score * 0.9,
                        reasoning=f"{name} has a lower SEO score; closing this gap may improve rankings",
                        impact_score=0.7,
                        agent_type=AgentType.COMPETITOR,
                        implementation_complexity="medium",
                        estimated_time=30,
                    )
                )

            # Suggest addressing content strategy gaps
            if content_strategy:
                recommendations.append(
                    AIRecommendation(
                        type="competitor_content_strategy",
                        original="",
                        suggested=f"Align content strategy with competitor: {content_strategy}",
                        confidence_score=competitor_result.confidence_score * 0.85,
                        reasoning=f"Learn from {name}'s content strategy to improve relevance",
                        impact_score=0.6,
                        agent_type=AgentType.COMPETITOR,
                        implementation_complexity="medium",
                        estimated_time=25,
                    )
                )

            # Quick wins from competitor weaknesses
            for weakness in weaknesses[:3]:
                recommendations.append(
                    AIRecommendation(
                        type="competitor_quick_win",
                        original="",
                        suggested=f"Address competitor weakness: {weakness}",
                        confidence_score=competitor_result.confidence_score * 0.8,
                        reasoning=f"Opportunity identified by analyzing {name}",
                        impact_score=0.5,
                        agent_type=AgentType.COMPETITOR,
                        implementation_complexity="low",
                        estimated_time=15,
                    )
                )

            # Opportunities from competitor gaps
            for opportunity in opportunities[:3]:
                recommendations.append(
                    AIRecommendation(
                        type="competitor_opportunity",
                        original="",
                        suggested=f"Leverage opportunity: {opportunity}",
                        confidence_score=competitor_result.confidence_score * 0.75,
                        reasoning=f"Identified from {name}'s competitive landscape",
                        impact_score=0.55,
                        agent_type=AgentType.COMPETITOR,
                        implementation_complexity="low",
                        estimated_time=20,
                    )
                )

        # 2️⃣ Recommendations based on overall gap analysis
        content_gaps = gap_analysis.get("content_gaps", [])
        technical_opps = gap_analysis.get("technical_opportunities", [])
        quick_wins = gap_analysis.get("quick_wins", [])
        long_term_opps = gap_analysis.get("long_term_opportunities", [])

        for gap in content_gaps[:5]:
            recommendations.append(
                AIRecommendation(
                    type="gap_content",
                    original="",
                    suggested=gap,
                    confidence_score=competitor_result.confidence_score * 0.9,
                    reasoning="Content gap identified compared to competitors",
                    impact_score=0.65,
                    agent_type=AgentType.COMPETITOR,
                    implementation_complexity="medium",
                    estimated_time=30,
                )
            )

        for opp in technical_opps[:3]:
            recommendations.append(
                AIRecommendation(
                    type="gap_technical",
                    original="",
                    suggested=opp,
                    confidence_score=competitor_result.confidence_score * 0.85,
                    reasoning="Technical SEO opportunity found vs competitors",
                    impact_score=0.6,
                    agent_type=AgentType.COMPETITOR,
                    implementation_complexity="medium",
                    estimated_time=25,
                )
            )

        for win in quick_wins[:3]:
            recommendations.append(
                AIRecommendation(
                    type="quick_win",
                    original="",
                    suggested=win,
                    confidence_score=competitor_result.confidence_score * 0.8,
                    reasoning="Quick improvement identified by competitor analysis",
                    impact_score=0.55,
                    agent_type=AgentType.COMPETITOR,
                    implementation_complexity="low",
                    estimated_time=15,
                )
            )

        for opp in long_term_opps[:3]:
            recommendations.append(
                AIRecommendation(
                    type="long_term_opportunity",
                    original="",
                    suggested=opp,
                    confidence_score=competitor_result.confidence_score * 0.75,
                    reasoning="Long-term opportunity identified from competitor landscape",
                    impact_score=0.5,
                    agent_type=AgentType.COMPETITOR,
                    implementation_complexity="medium",
                    estimated_time=40,
                )
            )

        return recommendations


    def _create_performance_recommendations(
    self, performance_result: AgentResult, audit_result: SEOAuditResult
) -> List[AIRecommendation]:
        recommendations = []
        data = performance_result.output_data or {}

        if traffic := data.get("traffic_prediction"):
            recommendations.append(
                AIRecommendation(
                    type="performance_traffic_prediction",
                    original="",
                    suggested=f"Expected traffic change: {traffic}%",
                    confidence_score=performance_result.confidence_score,
                    reasoning="Predicted traffic impact based on current performance metrics",
                    impact_score=0.8,
                    agent_type=AgentType.PERFORMANCE,
                    implementation_complexity="medium",
                    estimated_time=20,
                )
            )

        if timeline := data.get("timeline"):
            recommendations.append(
                AIRecommendation(
                    type="performance_timeline",
                    original="",
                    suggested=f"Expected ranking improvement timeline: {timeline}",
                    confidence_score=performance_result.confidence_score,
                    reasoning="Timeline prediction for SEO impact",
                    impact_score=0.7,
                    agent_type=AgentType.PERFORMANCE,
                    implementation_complexity="low",
                    estimated_time=10,
                )
            )

        if impact := data.get("mobile_desktop_impact"):
            recommendations.append(
                AIRecommendation(
                    type="performance_device_impact",
                    original="",
                    suggested=f"Device-specific impact: {impact}",
                    confidence_score=performance_result.confidence_score,
                    reasoning="Impact on mobile vs desktop performance",
                    impact_score=0.6,
                    agent_type=AgentType.PERFORMANCE,
                    implementation_complexity="medium",
                    estimated_time=15,
                )
            )

        if risk := data.get("risk_assessment"):
            recommendations.append(
                AIRecommendation(
                    type="performance_risk",
                    original="",
                    suggested=f"Risk assessment: {risk}",
                    confidence_score=performance_result.confidence_score,
                    reasoning="Potential SEO risks identified by performance agent",
                    impact_score=0.7,
                    agent_type=AgentType.PERFORMANCE,
                    implementation_complexity="medium",
                    estimated_time=15,
                )
            )

        return recommendations


    def _prioritize_recommendations(
        self, recommendations: List[AIRecommendation]
    ) -> List[AIRecommendation]:
        """Prioritize recommendations by impact and complexity"""
        if not recommendations:
            return []

        # Score each recommendation based on impact and complexity
        scored_recommendations = []
        for rec in recommendations:
            score = (
                rec.impact_score * 100
                - self._complexity_score(rec.implementation_complexity) * 10
            )
            scored_recommendations.append((score, rec))

        # Sort by score descending and return top recommendations
        # Sort by score descending and return all recommendations
        scored_recommendations.sort(key=lambda x: x[0], reverse=True)
        return [rec for score, rec in scored_recommendations]  # <-- all included

    def _complexity_score(self, complexity: str) -> int:
        """Convert complexity to numerical score for sorting"""
        complexity_scores = {"low": 1, "medium": 2, "high": 3}
        return complexity_scores.get(complexity.lower(), 2)

    async def _store_recommendations(
        self,
        url_id: str,
        recommendations: List[AIRecommendation],
        task_id: Optional[str],
    ):
        """Store recommendations in database"""
        try:
            # Prepare data for insertion
            recommendations_data = []
            for rec in recommendations:
                rec_dict = rec.dict()
                rec_dict["url_id"] = url_id
                if task_id:
                    rec_dict["task_id"] = task_id  # ✅ new
                rec_dict["created_at"] = datetime.now().isoformat()
                recommendations_data.append(rec_dict)

            # Store in Supabase
            if recommendations_data:
                await supabase_client.insert_into(
                    "ai_recommendations", recommendations_data
                )
                logger.info(
                    f"Stored {len(recommendations_data)} recommendations for URL ID: {url_id}  / Task {task_id}"
                )

            # Cache per task_id if available, else fallback to url_id
            cache_key = f"recommendations:{task_id or url_id}"
            await redis_client.setex(
                cache_key,
                24 * 60 * 60,
                json.dumps([rec.dict() for rec in recommendations], default=serialize),
            )
        except Exception as e:
            logger.error(f"Failed to store recommendations: {str(e)}")



    def _filter_by_optimization_level(
        self, recommendations: List[AIRecommendation], level: str
    ) -> List[AIRecommendation]:
        """Filter recommendations based on optimization level"""
        level_filters = {
            "basic": lambda r: r.implementation_complexity == "low",
            "standard": lambda r: r.implementation_complexity in ["low", "medium"],
            "advanced": lambda r: r.implementation_complexity
            in ["low", "medium", "high"],
            "aggressive": lambda r: True,
        }
        return [
            r for r in recommendations if level_filters.get(level, lambda r: True)(r)
        ]

    def _create_rollback_strategy(
        self, recommendations: List[AIRecommendation]
    ) -> Dict[str, Any]:
        """Create rollback strategy based on recommendation types"""
        strategy = {
            "backup_required": any(
                rec.implementation_complexity == "high" for rec in recommendations
            ),
            "step_by_step_rollback": len(recommendations) > 3,
            "monitoring_period_hours": (
                48 if any(rec.impact_score > 0.7 for rec in recommendations) else 24
            ),
        }

        # Add specific rollback instructions for different recommendation types
        strategy["instructions"] = []
        if any(rec.type == "schema_markup" for rec in recommendations):
            strategy["instructions"].append(
                "Schema markup can be removed without affecting page content"
            )

        if any(
            rec.type in ["title_optimization", "meta_description_optimization"]
            for rec in recommendations
        ):
            strategy["instructions"].append(
                "Meta tags can be reverted to previous values from backup"
            )

        return strategy

    def _calculate_risk_level(self, recommendations: List[AIRecommendation]) -> str:
        """Calculate overall risk level for deployment"""
        high_risk_count = sum(
            1 for rec in recommendations if rec.implementation_complexity == "high"
        )
        total_score = sum(rec.impact_score for rec in recommendations)

        if high_risk_count > 2 or total_score > 3.0:
            return "high"
        elif high_risk_count > 0 or total_score > 1.5:
            return "medium"
        else:
            return "low"

    def _identify_dependencies(
        self, recommendations: List[AIRecommendation]
    ) -> List[Dict[str, str]]:
        """Identify dependencies between recommendations"""
        dependencies = []

        # Schema recommendations might depend on content being stable
        schema_recs = [
            rec for rec in recommendations if rec.agent_type == AgentType.SCHEMA
        ]
        content_recs = [
            rec
            for rec in recommendations
            if rec.agent_type in [AgentType.KEYWORD, AgentType.SEMANTIC]
        ]

        if schema_recs and content_recs:
            dependencies.append(
                {
                    "from": "content_optimization",
                    "to": "schema_markup",
                    "reason": "Schema should be applied after content changes are finalized",
                }
            )

        return dependencies

    def _determine_deployment_order(
        self, recommendations: List[AIRecommendation]
    ) -> List[str]:
        """Determine the optimal deployment order"""
        # Group by type and complexity
        order_priority = {"low": 1, "medium": 2, "high": 3}

        type_priority = {"keyword": 1, "semantic": 2, "schema": 3}

        # Sort by complexity (low first) then by type (keyword first)
        sorted_recs = sorted(
            recommendations,
            key=lambda x: (
                order_priority.get(x.implementation_complexity, 2),
                type_priority.get(
                    x.agent_type.value.lower() if x.agent_type else "", 2
                ),
            ),
        )

        return [rec.id for rec in sorted_recs if rec.id]

    def _create_validation_rules(
        self, recommendations: List[AIRecommendation]
    ) -> List[Dict[str, Any]]:
        """Create validation rules to verify deployment success"""
        rules = []

        for rec in recommendations:
            if rec.type == "title_optimization":
                rules.append(
                    {
                        "type": "title_length",
                        "expected": f"Title should be between 50-60 characters: {rec.suggested}",
                        "validation": f"len('{rec.suggested}') >= 50 and len('{rec.suggested}') <= 60",
                    }
                )

            if rec.type == "meta_description_optimization":
                rules.append(
                    {
                        "type": "meta_length",
                        "expected": f"Meta description should be between 150-160 characters: {rec.suggested}",
                        "validation": f"len('{rec.suggested}') >= 150 and len('{rec.suggested}') <= 160",
                    }
                )

            if rec.type == "schema_markup":
                rules.append(
                    {
                        "type": "schema_validation",
                        "expected": "Schema should be valid JSON-LD",
                        "validation": "json.loads(rec.suggested) is not None"
                    }
                )

# schema_content is undefined in the validation string. Might need to reference actual recommendation content.


        return rules

    def _determine_page_type(self, page_data: PageSEOData) -> str:
        """Determine page type based on content"""
        if page_data.title and "blog" in page_data.title.lower():
            return "BlogPost"
        elif page_data.title and "product" in page_data.title.lower():
            return "Product"
        return "Article"

    def _create_fallback_result(self, agent_type: AgentType) -> AgentResult:
        """Create fallback result when agent fails"""
        return AgentResult(
            agent_type=agent_type,
            input_data={},
            output_data={},
            processing_time=0,
            confidence_score=0.0,
            cost_estimate=0,
            tokens_used=0,
        )

    async def _run_performance_agent(self, page_data: PageSEOData) -> AgentResult:
    # 1️⃣ Fetch live metrics (from AnalyticsHelper)
        current_metrics = await AnalyticsHelper.get_current_metrics(
            url=page_data.url,
            force_live=True,
            save_history=False,  # do not save automatically
        )

        # 2️⃣ Fetch historical metrics from Supabase (optional)
        historical_metrics = {}
        # if page_data.url_id:
        #     historical_rows = await supabase_client.get_historical_metrics(
        #         website_url=page_data.url,
        #         days=90
        #     )
        #     # Convert list -> dict for agent
        #     historical_metrics = {row["metric_name"]: row["value"] for row in historical_rows}

        # 3️⃣ Run agent with metrics
        result = await self.performance_agent.analyze_performance(
            current_metrics=current_metrics,
            historical_metrics=historical_metrics
        ) 
        
        # 4️⃣ Persist result in Supabase
        if page_data.url_id:
            payload = {
                    "url_id": page_data.url_id,
                    "current_metrics": current_metrics,
                    "historical_metrics": historical_metrics,
                    "output_data": result.output_data,
                    "confidence_score": float(result.confidence_score or 0),  # numeric column
                    "processing_time": int(float(result.processing_time or 0)),  # integer column
                    "created_at": datetime.utcnow().isoformat(),
                }
           
            existing = await supabase_client.fetch_one(
                "performance_predictions", {"url_id": page_data.url_id}
            )
            if existing:
                
                await supabase_client.update_table(
                    "performance_predictions", {"url_id": page_data.url_id}, payload
                )
            else:
                await supabase_client.insert_into("performance_predictions", payload)

        return result










# ✅ With these changes:

# Backend assigns task_id.

# _store_recommendations always persists recommendations, regardless of task ID.

# No auto-generated IDs in onpageseo.
# Suggested flow:

# User sees recommendations in a UI:

# List all suggested recommendations per page.

# Allow user to approve or reject each one.

# Persist the approved recommendations:

# Store the final approved set in a database table, e.g., approved_ai_recommendations.

# Only mark these as is_active_for_pixel = True (or similar).

# Pixel fetch logic:

# Modify get_active_optimizations to filter only approved recommendations.

# Example filter in Supabase:




# modify agentruns to include servicetype- 