"""
API Routes
==========
Endpoints for the Planning Board API
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from api.dependencies import verify_api_key
from models.requests import PlanGenerateRequest
from models.responses import (
    PlanGenerateResponse,
    AsyncTaskResponse,
    TaskStatusResponse,
    ErrorResponse,
)
from services.plan_generator import PlanGeneratorService
from core.exceptions import PlanningBoardException


router = APIRouter(tags=["Plans"])

# Router for static mock endpoints (no AI tokens consumed)
mock_router = APIRouter(prefix="/mock", tags=["Mock — .NET Backend Testing"])


@router.post(
    "/plans/generate",
    response_model=PlanGenerateResponse,
    responses={
        200: {"description": "Plan generated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
        502: {"model": ErrorResponse, "description": "LLM service error"},
    },
    summary="Generate Tasks from Plan",
    description="Analyze the plan and convert it into executable tasks with employee assignment"
)
async def generate_plan(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate tasks from a plan

    - **company_id**: Company ID
    - **team_id**: Team ID
    - **plan_text**: Strategic plan text
    """
    try:
        logger.info(f"Received plan generation request for team_id: {request.team_id}")

        # Initialize service
        service = PlanGeneratorService()

        # Generate plan
        result = await service.generate(
            company_id=request.company_id,
            team_id=request.team_id,
            plan_text=request.plan_text,
        )

        logger.info(f"Plan generated successfully: {result.plan_id}")
        return result

    except PlanningBoardException as e:
        logger.error(f"Planning board error: {e.message}")
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": type(e).__name__, "message": e.message, "details": e.details}
        )
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "InternalError", "message": str(e)}
        )


@router.post(
    "/plans/generate/async",
    response_model=AsyncTaskResponse,
    summary="Generate Tasks Asynchronously",
    description="Generate tasks asynchronously (Celery)"
)
async def generate_plan_async(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Generate tasks asynchronously - for large plans
    Returns a task_id for tracking
    """
    try:
        logger.info(f"Received async plan generation request for team_id: {request.team_id}")

        # Import Celery task
        from workers.tasks import generate_plan_task

        # Submit task to Celery
        task = generate_plan_task.delay(
            company_id=request.company_id,
            team_id=request.team_id,
            plan_text=request.plan_text,
        )

        logger.info(f"Task submitted: {task.id}")

        return AsyncTaskResponse(
            task_id=task.id,
            status="pending",
            message="Request received and processing"
        )

    except Exception as e:
        logger.exception(f"Failed to submit async task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"error": "TaskSubmissionError", "message": str(e)}
        )


@router.get(
    "/plans/status/{task_id}",
    response_model=TaskStatusResponse,
    summary="Check Async Task Status",
    description="Track the status of a generation task"
)
async def get_task_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Track the status of an asynchronous generation task
    """
    try:
        from workers.celery_app import celery_app

        task_result = celery_app.AsyncResult(task_id)

        response = TaskStatusResponse(
            task_id=task_id,
            status=task_result.status
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
            detail={"error": "StatusCheckError", "message": str(e)}
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check API health"
)
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "planning-board"}


# =====================================================
# Mock Endpoints — .NET Backend Testing
# Static responses, no AI tokens consumed
# =====================================================

_MOCK_PLAN_RESPONSE = {
    "plan_id": "plan_202606270312_aaca77",
    "plan_title": "Quarterly Sales Growth Initiative (20% Increase)",
    "status": "draft",
    "start_date": "2026-06-27",
    "deadline_date": "2026-11-04",
    "total_estimated_days": 131,
    "modules": [
        {
            "module_id": "mod_1",
            "module_name": "Market Research and Lead Generation",
            "tasks": [
                {
                    "task_id": "task_101",
                    "title": "Identify Target Customer Segments",
                    "description": "Conduct market research to identify high-potential customer segments for new business acquisition. Use CRM data, industry reports, and competitor analysis to refine targeting.",
                    "duration_days": 7,
                    "start_date": "2026-06-27",
                    "deadline_date": "2026-07-03",
                    "suggested_owner": {
                        "user_id": "Sales-tarek.nabil-employee",
                        "job_title": "Sales Operations Specialist",
                        "reason": "Sales Operations Specialist is suitable for Market Research and Data Analysis due to CRM and data management expertise."
                    },
                    "reason": None,
                    "dependencies": [],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_102",
                    "title": "Develop Lead Generation Strategy",
                    "description": "Create a tailored lead generation strategy for each identified customer segment, including sourcing channels (cold outreach, digital ads, referrals, etc.).",
                    "duration_days": 5,
                    "start_date": "2026-07-04",
                    "deadline_date": "2026-07-08",
                    "suggested_owner": {
                        "user_id": "Sales-ahmed.sales-teamleader",
                        "job_title": "Sales Team Leader",
                        "reason": "Sales Team Leader is suitable for Sales Strategy and Lead Generation due to broader sales oversight."
                    },
                    "reason": None,
                    "dependencies": ["task_101"],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_103",
                    "title": "Compile Lead Lists",
                    "description": "Compile and organize lead lists based on the strategy, ensuring accuracy and segmentation for targeted outreach. Use CRM tools to manage leads.",
                    "duration_days": 3,
                    "start_date": "2026-07-09",
                    "deadline_date": "2026-07-11",
                    "suggested_owner": {
                        "user_id": "Sales-tarek.nabil-employee",
                        "job_title": "Sales Operations Specialist",
                        "reason": "Sales Operations Specialist is suitable for Data Management and CRM Proficiency."
                    },
                    "reason": None,
                    "dependencies": ["task_102"],
                    "status": "to_do",
                    "priority": "high"
                }
            ]
        },
        {
            "module_id": "mod_2",
            "module_name": "Outreach and Initial Engagement",
            "tasks": [
                {
                    "task_id": "task_104",
                    "title": "Initial Cold Outreach to Leads",
                    "description": "Perform cold calls/emails to leads using personalized scripts. Schedule initial meetings or presentations with potential customers.",
                    "duration_days": 10,
                    "start_date": "2026-07-12",
                    "deadline_date": "2026-07-21",
                    "suggested_owner": {
                        "user_id": "Sales-aya.mansour-employee",
                        "job_title": "Telemarketing Agent",
                        "reason": "Telemarketing Agent is highly suitable for Telemarketing and Sales Outreach."
                    },
                    "reason": None,
                    "dependencies": [],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_105",
                    "title": "Follow-Up with Potential Customers",
                    "description": "Follow up with leads who showed initial interest, addressing objections and nurturing relationships to move them closer to a sale.",
                    "duration_days": 12,
                    "start_date": "2026-07-22",
                    "deadline_date": "2026-08-02",
                    "suggested_owner": {
                        "user_id": "Sales-mahmoud.ali-employee",
                        "job_title": "B2B Sales Representative",
                        "reason": "B2B Sales Representative is suitable for Sales Follow-Up and Relationship Management."
                    },
                    "reason": None,
                    "dependencies": ["task_104"],
                    "status": "to_do",
                    "priority": "high"
                }
            ]
        },
        {
            "module_id": "mod_3",
            "module_name": "Product Presentations and Proposals",
            "tasks": [
                {
                    "task_id": "task_106",
                    "title": "Prepare Customized Product Presentations",
                    "description": "Develop tailored product presentations for different customer segments, highlighting key benefits and addressing pain points.",
                    "duration_days": 8,
                    "start_date": "2026-08-03",
                    "deadline_date": "2026-08-10",
                    "suggested_owner": {
                        "user_id": "Sales-yasmine.ali-employee",
                        "job_title": "Sales Account Manager",
                        "reason": "Sales Account Manager is suitable for Sales Presentation and Content Creation."
                    },
                    "reason": None,
                    "dependencies": [],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_107",
                    "title": "Conduct Product Demonstrations",
                    "description": "Deliver live product demonstrations to potential customers, either in-person or virtually, and gather feedback.",
                    "duration_days": 10,
                    "start_date": "2026-08-11",
                    "deadline_date": "2026-08-20",
                    "suggested_owner": {
                        "user_id": "Sales-mahmoud.ali-employee",
                        "job_title": "B2B Sales Representative",
                        "reason": "B2B Sales Representative is suitable for Sales Demonstration and Customer Engagement."
                    },
                    "reason": None,
                    "dependencies": ["task_106"],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_108",
                    "title": "Generate and Send Proposals",
                    "description": "Create and send customized proposals to qualified leads, including pricing, terms, and next steps for negotiation.",
                    "duration_days": 7,
                    "start_date": "2026-08-21",
                    "deadline_date": "2026-08-27",
                    "suggested_owner": {
                        "user_id": "Sales-kareem.salah-employee",
                        "job_title": "Sales Executive",
                        "reason": "Sales Executive is suitable for Proposal Writing and Sales Negotiation."
                    },
                    "reason": None,
                    "dependencies": ["task_107"],
                    "status": "to_do",
                    "priority": "high"
                }
            ]
        },
        {
            "module_id": "mod_4",
            "module_name": "Sales Negotiation and Closing",
            "tasks": [
                {
                    "task_id": "task_109",
                    "title": "Negotiate Contract Terms",
                    "description": "Engage in contract negotiations with potential customers, addressing concerns and finalizing terms that are mutually beneficial.",
                    "duration_days": 15,
                    "start_date": "2026-08-28",
                    "deadline_date": "2026-09-11",
                    "suggested_owner": {
                        "user_id": "Sales-yasmine.ali-employee",
                        "job_title": "Sales Account Manager",
                        "reason": "Sales Account Manager is suitable for Sales Negotiation and Contract Review."
                    },
                    "reason": None,
                    "dependencies": [],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_110",
                    "title": "Close Sales Deals",
                    "description": "Finalize sales deals by securing signatures, processing orders, and ensuring smooth onboarding for new customers.",
                    "duration_days": 12,
                    "start_date": "2026-09-12",
                    "deadline_date": "2026-09-23",
                    "suggested_owner": {
                        "user_id": "Sales-maha.ali-employee",
                        "job_title": "Inside Sales Representative",
                        "reason": "Inside Sales Representative is suitable for Sales Closing and Order Processing."
                    },
                    "reason": None,
                    "dependencies": ["task_109"],
                    "status": "to_do",
                    "priority": "high"
                }
            ]
        },
        {
            "module_id": "mod_5",
            "module_name": "Customer Onboarding and Support",
            "tasks": [
                {
                    "task_id": "task_111",
                    "title": "Onboard New Customers",
                    "description": "Provide new customers with onboarding support, including training, setup, and ensuring they are satisfied with the product/service.",
                    "duration_days": 10,
                    "start_date": "2026-09-24",
                    "deadline_date": "2026-10-03",
                    "suggested_owner": {
                        "user_id": "Sales-reem.hassan-employee",
                        "job_title": "Customer Success Specialist",
                        "reason": "Customer Success Specialist is suitable for Customer Onboarding and Support Coordination."
                    },
                    "reason": None,
                    "dependencies": [],
                    "status": "to_do",
                    "priority": "low"
                },
                {
                    "task_id": "task_112",
                    "title": "Monitor Customer Satisfaction",
                    "description": "Track customer satisfaction through surveys, check-ins, and feedback loops to ensure long-term success and retention.",
                    "duration_days": 5,
                    "start_date": "2026-10-04",
                    "deadline_date": "2026-10-08",
                    "suggested_owner": {
                        "user_id": "Sales-reem.hassan-employee",
                        "job_title": "Customer Success Specialist",
                        "reason": "Customer Success Specialist is suitable for Customer Success and Feedback Analysis."
                    },
                    "reason": None,
                    "dependencies": ["task_111"],
                    "status": "to_do",
                    "priority": "low"
                }
            ]
        },
        {
            "module_id": "mod_6",
            "module_name": "Performance Reporting and Analysis",
            "tasks": [
                {
                    "task_id": "task_113",
                    "title": "Track Sales Metrics in Real-Time",
                    "description": "Monitor daily/weekly sales metrics (e.g., conversion rates, deal sizes, lead response times) using CRM and analytics tools.",
                    "duration_days": 15,
                    "start_date": "2026-10-09",
                    "deadline_date": "2026-10-23",
                    "suggested_owner": {
                        "user_id": "Sales-hany.adel-employee",
                        "job_title": "Sales Support Assistant",
                        "reason": "Rebalanced to Sales Support Assistant for even distribution (Job Title match for Sales Analytics, CRM Management)"
                    },
                    "reason": None,
                    "dependencies": [],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_114",
                    "title": "Prepare Quarterly Sales Report",
                    "description": "Compile a detailed report on sales performance, including key indicators (e.g., revenue growth, customer acquisition cost, conversion rates).",
                    "duration_days": 7,
                    "start_date": "2026-10-24",
                    "deadline_date": "2026-10-30",
                    "suggested_owner": {
                        "user_id": "Sales-tarek.nabil-employee",
                        "job_title": "Sales Operations Specialist",
                        "reason": "Sales Operations Specialist is suitable for Reporting and Data Visualization."
                    },
                    "reason": None,
                    "dependencies": ["task_113"],
                    "status": "to_do",
                    "priority": "high"
                },
                {
                    "task_id": "task_115",
                    "title": "Analyze Performance and Identify Trends",
                    "description": "Analyze sales data to identify trends, strengths, and areas for improvement. Provide actionable insights for future strategies.",
                    "duration_days": 5,
                    "start_date": "2026-10-31",
                    "deadline_date": "2026-11-04",
                    "suggested_owner": {
                        "user_id": "Sales-omar.kamal-employee",
                        "job_title": "Senior Sales Specialist",
                        "reason": "Senior Sales Specialist is suitable for Data Analysis and Strategic Planning."
                    },
                    "reason": None,
                    "dependencies": ["task_114"],
                    "status": "to_do",
                    "priority": "high"
                }
            ]
        }
    ],
    "timeline": [
        {
            "phase": "Market Research and Lead Generation",
            "start_day": 1,
            "end_day": 15,
            "start_date": "2026-06-27",
            "end_date": "2026-07-11"
        },
        {
            "phase": "Outreach and Initial Engagement",
            "start_day": 16,
            "end_day": 37,
            "start_date": "2026-07-12",
            "end_date": "2026-08-02"
        },
        {
            "phase": "Product Presentations and Proposals",
            "start_day": 38,
            "end_day": 62,
            "start_date": "2026-08-03",
            "end_date": "2026-08-27"
        },
        {
            "phase": "Sales Negotiation and Closing",
            "start_day": 63,
            "end_day": 89,
            "start_date": "2026-08-28",
            "end_date": "2026-09-23"
        },
        {
            "phase": "Customer Onboarding and Support",
            "start_day": 90,
            "end_day": 104,
            "start_date": "2026-09-24",
            "end_date": "2026-10-08"
        },
        {
            "phase": "Performance Reporting and Analysis",
            "start_day": 105,
            "end_day": 131,
            "start_date": "2026-10-09",
            "end_date": "2026-11-04"
        }
    ]
}


@mock_router.post(
    "/plans/generate",
    response_model=PlanGenerateResponse,
    summary="Generate Tasks from Plan (Static Mock)",
    description="Returns a static plan response for .NET backend testing. No AI tokens consumed."
)
async def mock_generate_plan(
    request: PlanGenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Static mock endpoint for .NET backend testing.

    Returns a pre-built plan response without calling the LLM.
    Useful for integration testing without consuming AI tokens.
    """
    logger.info(f"Mock plan generation request received for team_id: {request.team_id}")
    return PlanGenerateResponse(**_MOCK_PLAN_RESPONSE)
