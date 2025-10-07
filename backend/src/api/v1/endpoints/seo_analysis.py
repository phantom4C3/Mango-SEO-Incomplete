# backend/src/api/endpoints/seo_analysis.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from ....services.task_service import TaskService
from ....services.seo_workflow_service import SEOWorkflowService
from shared_models import (
    SEOAnalysisRequest,
    SEOAnalysisResponse,
    TaskStatus,
    BatchAnalysisRequest,
    BatchAnalysisResponse,
)
from ....core.auth import get_current_user, User

router = APIRouter()


@router.post("/seo/analyze", response_model=SEOAnalysisResponse)
async def analyze_website(
    request: SEOAnalysisRequest,
    background_tasks: BackgroundTasks,
    seo_service: SEOWorkflowService = Depends(SEOWorkflowService),
    current_user: User = Depends(get_current_user),  # ✅ JWT auth
):

    """
    Trigger a single website SEO analysis.
    """
    try:
        # ✅ Always use TaskService for task creation
        task_id = await TaskService.create_task(
            user_id=request.user_id,
            task_type="seo_analysis",
            parameters={
                "url": request.url,
                "depth": request.depth,
                "analysis_type": request.analysis_type,
            },
        )

        # Run workflow in background
        background_tasks.add_task(
            seo_service.initiate_seo_analysis,
            request.url,
            request.user_id,
            task_id,
            request.depth,
            request.analysis_type,
        )

        return SEOAnalysisResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="SEO analysis started",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initiate SEO analysis: {str(e)}")


@router.get("/seo/analysis/{task_id}")
async def get_analysis_status(
    task_id: str,
    current_user: User = Depends(get_current_user),  # ✅ JWT auth
):

    """
    Get status and results of SEO analysis from TaskService.
    """
    task = await TaskService.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access")
    return task



@router.post("/seo/batch/analyze")
async def batch_analyze_website(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    seo_service: SEOWorkflowService = Depends(SEOWorkflowService),
    current_user: User = Depends(get_current_user),  # ✅ JWT auth
):

    """
    Trigger a batch SEO analysis.
    """
    # ✅ Always use TaskService for task creation
    task_id = await TaskService.create_task(
        user_id=current_user.id,  # use JWT user
        task_type="batch_seo_analysis",
        parameters={
            "website_id": str(request.website_id),
            "max_pages": request.max_pages,
            "analysis_type": request.analysis_type,
        },
    )


    background_tasks.add_task(
        seo_service.process_batch_analysis,
        str(request.website_id),
        task_id,
        request.max_pages,
    )

    return BatchAnalysisResponse(task_id=task_id, status="pending")




