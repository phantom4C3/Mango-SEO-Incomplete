# onpageseo-service/app/api/v1/endpoints/analyze.py
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Depends
from pydantic import HttpUrl
from typing import Dict, Any
import logging
import httpx
from datetime import datetime
import asyncio
from uuid import uuid4
import json
from fastapi.encoders import jsonable_encoder

from ....services.analyzer import SEOAnalyzer
from ....services.recommender import SEORecommender
from ....clients.redis_client import redis_client
from shared_models.models import (
    SEOAnalysisRequest,
    SEOAnalysisResponse,
    AuditStatus,
    BatchAuditResponse,
    BatchAuditRequest
)
from fastapi import HTTPException
from ....core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/seo", tags=["SEO Analysis"])



async def _cache_result(cache_key: str, data: Dict[str, Any], ttl: int = 3600):
    """Cache result in Redis"""
    try:
        encoded = jsonable_encoder(data)  # ✅ converts Pydantic models to dict
        await redis_client.setex(cache_key, ttl, encoded)
    except Exception as e:
        logger.warning(f"Failed to cache result for {cache_key}: {str(e)}")


@router.post("/analyze", response_model=SEOAnalysisResponse)
async def analyze_page(
    request: SEOAnalysisRequest,
    background_tasks: BackgroundTasks, 
    task_id: str = None,
):

    """
    Analyze a webpage for SEO issues and optionally generate recommendations.
    """
    
    print(f"[API] /seo/analyze called with URL={request.url} task_id={task_id}")

    if not request.url and not request.html:
        raise HTTPException(
            status_code=422, detail="Either 'url' or 'html' must be provided"
        )

    # cache_key = f"seo:analysis:{request.url or 'raw'}"
    # if not request.force_refresh:
    #     cached = await redis_client.get(cache_key)
    #     if cached:
    #         cached_data = (
    #             json.loads(cached) if isinstance(cached, (str, bytes)) else cached
    #         )
    #         cached_data["cached"] = True
    #         return SEOAnalysisResponse(**cached_data)
    #     print(f"[API] Returning cached result for {cache_key}")
    
    
        # Generate cache key for this URL
    cache_key = f"seo:analysis:{request.url or 'raw'}"

    # Optional: fetch cached data just to log, but do NOT return it
    if not request.force_refresh:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"[Cache] Found cached result for {request.url}, but will run fresh analysis")



    # Step 1: Use the analyzer's fetch method which handles redirects properly
    analyzer = SEOAnalyzer()

    # Get HTML content - let the analyzer handle URL fetching with redirects
    html_content = request.html
    if not html_content and request.url:
        try:
            
            print(f"[Analyzer] Fetching HTML content for {request.url}")

            html_content = await analyzer._fetch_url_content(str(request.url))
        except httpx.HTTPStatusError as e:
            # Handle blocked sites specifically
            if e.response.status_code in [403, 401, 429]:
                logger.warning(
                    f"[Blocked/Rate-Limited] URL: {request.url} Status: {e.response.status_code}"
                )
                raise HTTPException(
                    status_code=403,
                    detail=f"Access blocked or rate-limited for URL: {request.url}",
                )
            raise
        except Exception as e:
            print(f"[Analyzer] Failed to fetch HTML for {request.url}: {str(e)}")

            logger.error(f"Failed to fetch URL {request.url}: {str(e)}")
            raise HTTPException(
                status_code=400, detail=f"Could not fetch URL: {str(e)}"
            )
            

    print("[Analyzer] Running SEOAnalyzer.analyze")

    # Step 2: Run Analyzer → SEOAuditResult
    analysis_result = await analyzer.analyze(
        url=str(request.url) if request.url else None,
        html_content=html_content,
        task_id=task_id,
    )

    print(f"[Analyzer] Analysis completed. AI triggers: {analysis_result.ai_triggers}")

    print("[Recommender] Running SEORecommender.generate_recommendations")

    # Step 3: Run Recommender
    recommender = SEORecommender()
    recommendations = await recommender.generate_recommendations(
        analysis_result, task_id=task_id
    )

    print(f"[Recommender] Recommendations generated: {len(recommendations)} items")

    print("[API] Returning final SEOAnalysisResponse")

    response_data = {
        "audit_id": str(uuid4()),
        "url": analysis_result.url,
        "url_id": analysis_result.url_id,
        "status": AuditStatus.COMPLETED,
        "score": analysis_result.overall_score,
        "issues": analysis_result.issues,
        "issues_count": len(analysis_result.issues),
        "warnings": analysis_result.warnings,
        "warnings_count": len(analysis_result.warnings),
        "recommendations": recommendations,
        "cached": False,
        "task_id": task_id,
        "ai_agents_used": analysis_result.ai_triggers,  
        "metrics": analysis_result.metrics,   
        "page_data": analysis_result.page_data,   
        "analyzer_context": analysis_result.analyzer_context,
        "extracted_keywords": analysis_result.extracted_keywords,
        "industry": analysis_result.industry,
        "generated_at": datetime.now().isoformat(),
    }

    # Step 4: Cache locally
    background_tasks.add_task(_cache_result, cache_key, response_data)

    return SEOAnalysisResponse(**response_data)


@router.post("/analyze/batch")
async def analyze_batch(
    request: BatchAuditRequest,
):

    """
    Batch analyze multiple URLs sequentially to avoid hitting AI API limits.
    """

    urls = request.urls
    task_ids = getattr(request, "task_ids", [None] * len(urls))  # Optional per-URL task IDs

    if len(urls) > 10:
        raise HTTPException(
            status_code=400,
            detail="You can analyze a maximum of 10 URLs per batch request."
        )

    results = []

    for i, url in enumerate(urls):
        task_id = task_ids[i] if i < len(task_ids) else None

        url_str = str(url)  # <-- convert HttpUrl to string
        print(f"[Batch] Processing URL {i+1}/{len(urls)}: {url} with task_id={task_id}")

        try:
            analyzer = SEOAnalyzer()
            try:
                html = await analyzer._fetch_url_content(url_str)  # <-- use url_str
                print(f"[Batch] HTML fetched for {url_str} ({len(html)} bytes)")
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [403, 401, 429]:
                    logger.warning(f"[Blocked/Rate-Limited] {url} → {e.response.status_code}")
                    results.append({
                        "url": url,
                        "task_id": task_id,
                        "error": f"Blocked (HTTP {e.response.status_code})"
                    })
                    continue
                raise
            except Exception as e:
                results.append({
                    "url": url,
                    "task_id": task_id,
                    "error": str(e)
                })
                continue

            # Run analyzer
            analysis_result = await analyzer.analyze(url=url_str, html_content=html, task_id=task_id)  # <-- url_str
            print(f"[Batch] Analyzer completed for {url_str}")


            # Run recommender
            recommender = SEORecommender()
            recommendations = await recommender.generate_recommendations(analysis_result, task_id=task_id)

            results.append(
                SEOAnalysisResponse(
                    audit_id=str(uuid4()),
                    url=analysis_result.url,
                    url_id=analysis_result.url_id,
                    status=AuditStatus.COMPLETED,
                    score=analysis_result.overall_score,
                    issues=analysis_result.issues,
                    issues_count=len(analysis_result.issues),
                    warnings=analysis_result.warnings,
                    warnings_count=len(analysis_result.warnings),
                    recommendations=recommendations,
                    cached=False,
                    task_id=task_id,
                    ai_agents_used=analysis_result.ai_triggers,
                    metrics=analysis_result.metrics,
                    page_data=analysis_result.page_data,
                    analyzer_context=analysis_result.analyzer_context,
                    extracted_keywords=analysis_result.extracted_keywords,
                    industry=analysis_result.industry,
                    generated_at=datetime.now(),
                )
            )

        except Exception as e:
            results.append(
                SEOAnalysisResponse(
                    audit_id=str(uuid4()),
                    url=url,
                    status=AuditStatus.FAILED,
                    score=0,
                    issues=[],
                    issues_count=0,
                    warnings=[],
                    warnings_count=0,
                    recommendations=[],
                    cached=False,
                    task_id=task_id,
                    ai_agents_used=[],
                    metrics={},
                    page_data={},
                    analyzer_context={},
                    extracted_keywords=[],
                    industry=None,
                    generated_at=datetime.now(),
                )
            )

    # Compute summary
    success_count = sum(1 for r in results if getattr(r, "status", None) == AuditStatus.COMPLETED)
    fail_count = len(results) - success_count

    summary = BatchAuditResponse(
        batch_id=str(uuid4()),
        total_urls=len(urls),
        processed_urls=len(results),
        successful_urls=success_count,
        failed_urls=fail_count,
        total_issues_found=sum(len(r.issues) for r in results if hasattr(r, "issues")),
        average_score=sum(r.score for r in results if hasattr(r, "score")) / max(1, success_count),
        status=AuditStatus.COMPLETED,
        started_at=datetime.now(),
        completed_at=datetime.now(),
    )

    return {"status": "completed", "results": results, "summary": summary}


# validate each and every request using header, secret, security.py 