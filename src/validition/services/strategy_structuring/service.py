"""
Strategy Structuring Agent - Service
"""
import asyncio
from crewai import Agent, Crew, LLM, Task
from loguru import logger
from pydantic import ValidationError

from core.config import settings
from core.exceptions import StrategyStructuringException
from models.schemas import StrategyOutput
from models.entities import StructuredPlan, PrecedentEngineInput, PrimaryAction, PrimaryActionDetails, \
    ResourceSimulatorInput, ActionItem, ResourceRequirements
from .prompts import AGENT_ROLE, AGENT_GOAL, AGENT_BACKSTORY, TASK_DESCRIPTION


class StrategyStructuringService:
    """Service for structuring raw strategy text into a structured plan."""

    def __init__(self):
        self._llm = LLM(
            model=f"groq/{settings.GROQ_MODEL}",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        self._agent = Agent(
            role=AGENT_ROLE,
            goal=AGENT_GOAL,
            backstory=AGENT_BACKSTORY,
            llm=self._llm,
            verbose=False,
            allow_delegation=False,
            tools=[],
            max_iter=1,
        )

    async def structure(self, user_request: str) -> StructuredPlan:
        logger.info("Starting strategy structuring...")

        task = Task(
            description=TASK_DESCRIPTION,
            expected_output="Strict structured JSON",
            agent=self._agent,
            output_json=StrategyOutput,
        )
        crew = Crew(agents=[self._agent], tasks=[task], verbose=False)

        try:
            result = await asyncio.to_thread(
                crew.kickoff, inputs={"user_plan": user_request}
            )
        except Exception as e:
            logger.error(f"Strategy structuring crew failed: {e}")
            raise StrategyStructuringException(
                message=f"CrewAI execution failed: {str(e)}",
            )

        try:
            structured = StrategyOutput.model_validate_json(result.raw)
        except ValidationError as e:
            logger.error(f"Strategy output validation failed: {e}")
            raise StrategyStructuringException(
                message="Schema validation failed for structuring output",
                details={"raw_output": result.raw[:500]},
            )

        plan = self._to_entity(structured)
        logger.info("Strategy structuring completed successfully")
        return plan

    @staticmethod
    def _to_entity(schema: StrategyOutput) -> StructuredPlan:
        pe = schema.precedent_engine_input
        rs = schema.resource_simulator_input

        return StructuredPlan(
            precedent_engine_input=PrecedentEngineInput(
                strategy_type=pe.strategy_type,
                decision_category=pe.decision_category,
                primary_action=PrimaryAction(
                    action_type=pe.primary_action.action_type,
                    details=PrimaryActionDetails(
                        location=pe.primary_action.details.location,
                        channel=pe.primary_action.details.channel,
                    ),
                ),
            ),
            resource_simulator_input=ResourceSimulatorInput(
                all_actions=[
                    ActionItem(action_type=a.action_type, details=a.details)
                    for a in rs.all_actions
                ],
                resource_requirements=ResourceRequirements(
                    financial=rs.resource_requirements.financial,
                    human=rs.resource_requirements.human,
                    operational=rs.resource_requirements.operational,
                ),
                time_horizon=rs.time_horizon,
            ),
        )


strategy_structuring_service = StrategyStructuringService()
