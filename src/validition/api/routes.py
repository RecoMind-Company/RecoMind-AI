"""
API Routes
==========
Endpoints for the Validation API
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.dependencies import verify_api_key
from models.requests import ValidationRequest
from models.responses import (
    ValidationResponse,
    AsyncTaskResponse,
    TaskStatusResponse,
    ErrorResponse,
)
from services.validation_pipeline import ValidationPipelineService
from core.exceptions import ValidationException


router = APIRouter(tags=["Validation"])

mock_router = APIRouter(prefix="/mock", tags=["Mock — .NET Backend Testing"])


@router.post(
    "/validate",
    response_model=ValidationResponse,
    responses={
        200: {"description": "Validation completed successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        502: {"model": ErrorResponse, "description": "LLM service error"},
    },
    summary="Run Validation Pipeline",
    description="Run the full validation pipeline: strategy structuring, precedent engine, and resource simulator",
)
async def run_validation(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Run the full validation pipeline synchronously.

    - **company_id**: Company ID for automatic company info retrieval
    - **team_id**: Team ID for automatic report retrieval
    - **user_request**: Strategic plan or business decision text to validate
    """
    try:
        logger.info(f"Validation request for company_id: {request.company_id}, team_id: {request.team_id}")

        service = ValidationPipelineService()
        result = await service.run(
            company_id=request.company_id,
            team_id=request.team_id,
            user_request=request.user_request,
        )

        logger.info("Validation completed successfully")
        return result

    except ValidationException as e:
        logger.error(f"Validation error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": type(e).__name__, "message": e.message, "details": e.details},
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": str(e)},
        )


@router.post(
    "/validate/async",
    response_model=AsyncTaskResponse,
    summary="Run Validation Asynchronously",
    description="Run the validation pipeline asynchronously (Celery) for large requests",
)
async def run_validation_async(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Run the validation pipeline asynchronously.
    Returns a task_id for tracking progress.
    """
    try:
        logger.info(f"Async validation request for company_id: {request.company_id}, team_id: {request.team_id}")

        from workers.tasks import run_validation_task

        task = run_validation_task.delay(
            company_id=request.company_id,
            team_id=request.team_id,
            user_request=request.user_request,
        )

        logger.info(f"Task submitted: {task.id}")

        return AsyncTaskResponse(
            task_id=task.id,
            status="pending",
            message="Validation request received and processing",
        )

    except Exception as e:
        logger.exception(f"Failed to submit async task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "TaskSubmissionError", "message": str(e)},
        )


@router.get(
    "/validate/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Check Async Task Status",
    description="Track the status of a validation task",
)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key),
):
    """
    Track the status of an asynchronous validation task.
    """
    try:
        from workers.celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status,
        )

        if task_result.ready():
            if task_result.successful():
                response.result = task_result.result
                response.progress = 100
            else:
                response.error = str(task_result.result)
        elif task_result.status == "PROGRESS":
            response.progress = task_result.info.get("progress", 0)

        return response

    except Exception as e:
        logger.exception(f"Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "StatusCheckError", "message": str(e)},
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check API health",
)
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "validation"}


# =====================================================
# Mock Endpoint — .NET Backend Testing
# Static response, no AI tokens consumed
# =====================================================

_MOCK_VALIDATION_RESPONSE = {
    "status": "completed",
    "company_info": {
        "name": "E-Commerce Company",
        "industry": "E-Commerce",
        "size": "200",
        "description": "E-Commerce Company In mansoura",
        "country": "mansoura",
    },
    "structured_plan": {
        "precedent_engine_input": {
            "strategy_type": "Sales Strategy",
            "decision_category": "Revenue Growth",
            "primary_action": {
                "action_type": "Increase Sales",
                "details": {"location": "", "channel": ""},
            },
            "company_context": {},
        },
        "resource_simulator_input": {
            "all_actions": [
                {"action_type": "Target New Customers", "details": {}},
                {"action_type": "Follow Up With Potential Customers", "details": {}},
                {"action_type": "Conduct Product Presentations", "details": {}},
                {"action_type": "Negotiate Contracts", "details": {}},
                {"action_type": "Complete Sales", "details": {}},
                {"action_type": "Prepare Final Report", "details": {}},
            ],
            "resource_requirements": {
                "financial": [],
                "human": [],
                "operational": [],
            },
            "time_horizon": "Short Term",
        },
    },
    "precedent_result": {
        "precedent_summary": {
            "precedent_exists": True,
            "cases_analyzed": 3,
            "context_match_level": "High",
            "confidence_score": 73.51,
        },
        "outcomes": {"success": 1, "partial_success": 1, "failure": 1},
        "what_worked": [
            "grew youtube",
            "youtube channel",
            "channel blog",
            "blog successful",
            "successful ecommerce",
        ],
        "what_failed": [
            "tolerated rampant",
            "rampant fraud",
            "fraud china",
            "china minimize",
            "minimize revenue",
        ],
        "key_insights": {
            "success_factors": [
                "Humble beginnings and ability to make thousands of dollars in sales",
            ],
            "failure_factors": [
                "To minimize revenue impact and safeguard billions in revenue",
                "Lack of sales after listing on Amazon, prompting changes to the business strategy",
            ],
        },
        "cases": [
            {
                "company": "Beardbrand",
                "outcome": "Success",
                "what_happened": "Grew from a YouTube channel and blog into a successful eCommerce business",
                "reason": "Humble beginnings and ability to make thousands of dollars in sales",
            },
            {
                "company": "Meta",
                "outcome": "Partial",
                "what_happened": "Tolerated rampant ad fraud from China",
                "reason": "To minimize revenue impact and safeguard billions in revenue",
            },
            {
                "company": "Unspecified pickleball paddle business",
                "outcome": "Failure",
                "what_happened": "Sold exactly four units on Amazon in five months",
                "reason": "Lack of sales after listing on Amazon, prompting changes to the business strategy",
            },
        ],
    },
    "resource_simulation_result": {
        "financial_resources": {
            "is_sufficient": True,
            "status": "Sufficient",
            "why": [
                "The company has generated significant revenue, with $2.43 billion in total revenue and a high average order value of $20,733.14, indicating a strong financial foundation.",
                "The company's revenue growth trajectory shows acceleration potential, with 250%+ growth in 2014 compared to 2011-2012 baselines.",
            ],
            "key_metrics": {
                "total_revenue": "$2.43 billion",
                "average_order_value": "$20,733.14",
            },
        },
        "human_resources": {
            "is_sufficient": True,
            "status": "Sufficient",
            "why": [
                "The company has a size of 200 employees, which is a medium-sized company, indicating a reasonable number of staff to support the plan's requirements.",
                "The company's operational efficiency, with 100% shipping on-time delivery and 7-day average order processing, suggests a well-organized and capable team.",
            ],
            "key_metrics": {"company_size": "200 employees"},
        },
        "operational_resources": {
            "is_sufficient": True,
            "status": "Ready",
            "why": [
                "The company description mentions an e-commerce company, indicating a readiness for digital operations and potential for online sales and marketing.",
                "The company's operational excellence, with perfect shipping performance and high customer value, demonstrates a strong foundation for executing the plan.",
            ],
            "key_metrics": None,
        },
        "overall_execution_verdict": {
            "can_execute_plan": True,
            "blocking_factors": [],
        },
    },
    "market_trend_result": {
        "trend_summary": {
            "market_direction": "Growing",
            "growth_rate": "16.46% CAGR",
            "trend_confidence": 90,
            "timing_assessment": "Favorable with high growth rate and increasing online sales",
        },
        "key_trends": [
            "Generative AI and zero-click search",
            "Media networks driving incremental growth",
            "Secondhand and sustainable e-commerce",
        ],
        "opportunities": [
            "Increasing online sales with a projected global e-commerce market worth $6.3 trillion",
            "Expanding into new markets with high growth rates",
            "Adopting emerging trends like generative AI and zero-click search",
        ],
        "risks": [
            "Subdued e-commerce spending trends",
            "High competition level in mature markets",
            "Rapidly changing consumer behavior and preferences",
        ],
        "location_insights": {
            "location": "Global, with specific insights for the US and Vietnam",
            "market_maturity": "Growing",
            "competition_level": "Medium",
        },
        "recommendation": "Invest in emerging trends, expand into new markets, and optimize online sales strategies to capitalize on the growing e-commerce market",
    },
    "validation_report": {
        "executive_summary": "The validation report indicates a favorable decision to increase company sales by 20% in the next quarter, with a high confidence score of 85 based on precedent analysis, resource simulation, and market trend analysis. The company has sufficient financial, human, and operational resources to execute the plan, and the market trend is growing with a 16.46% CAGR. However, there are risks associated with subdued e-commerce spending trends, high competition level in mature markets, and rapidly changing consumer behavior and preferences.",
        "validation_decision": "Favorable",
        "confidence_score": 85,
        "key_findings": {
            "precedent_analysis": "The precedent analysis shows a high context match level of 73.51, with 1 success, 1 partial success, and 1 failure case. The key success factors include humble beginnings and ability to make thousands of dollars in sales, while the failure factors include lack of sales after listing on Amazon and tolerated rampant ad fraud from China.",
            "resource_assessment": "The resource simulation results indicate that the company has sufficient financial, human, and operational resources to execute the plan, with a total revenue of $2.43 billion, an average order value of $20,733.14, and a company size of 200 employees.",
            "market_trends": "The market trend analysis shows a growing market with a 16.46% CAGR, and key trends include generative AI and zero-click search, media networks driving incremental growth, and secondhand and sustainable e-commerce. The location insights indicate a growing market in the US and Vietnam, with a medium competition level.",
        },
        "recommendations": [
            "Invest in emerging trends like generative AI and zero-click search to capitalize on the growing e-commerce market",
            "Expand into new markets with high growth rates, such as the US and Vietnam",
            "Optimize online sales strategies to increase sales by 20% in the next quarter",
            "Monitor and adapt to rapidly changing consumer behavior and preferences",
            "Develop a contingency plan to mitigate risks associated with subdued e-commerce spending trends and high competition level in mature markets",
        ],
        "risk_factors": [
            "Subdued e-commerce spending trends",
            "High competition level in mature markets",
            "Rapidly changing consumer behavior and preferences",
            "Lack of sales after listing on Amazon",
            "Tolerated rampant ad fraud from China",
        ],
        "next_steps": [
            "Conduct further market research to identify new opportunities and trends",
            "Develop a detailed plan to invest in emerging trends and expand into new markets",
            "Assign a team to optimize online sales strategies and monitor consumer behavior and preferences",
            "Establish a contingency plan to mitigate risks and ensure the company's sales goals are met",
            "Schedule regular progress meetings to review the plan's execution and make adjustments as needed",
        ],
    },
}


@mock_router.post(
    "/validate",
    response_model=ValidationResponse,
    summary="Run Validation (Static Mock)",
    description="Returns a static validation response for .NET backend testing. No AI tokens consumed.",
)
async def mock_validate(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key),
):
    """Static mock endpoint for .NET backend testing."""
    logger.info(f"Mock validation request received for team_id: {request.team_id}")
    return ValidationResponse(**_MOCK_VALIDATION_RESPONSE)
