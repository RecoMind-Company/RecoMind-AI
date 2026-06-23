"""
Plan Parser Service
===================
تحليل الخطة باستخدام LLM وتحويلها لـ Modules و Tasks
"""

from typing import List
from loguru import logger

from llm.client import llm_client
from llm.prompts import PLAN_PARSER_SYSTEM_PROMPT, PLAN_PARSER_USER_PROMPT
from models.entities import Module, Task, ParsedPlan
from utils.id_generator import generate_module_id, generate_task_id
from core.exceptions import LLMException


class PlanParserService:
    """خدمة تحليل الخطط"""
    
    def __init__(self):
        self.llm = llm_client
    
    async def parse(self, plan_text: str) -> ParsedPlan:
        """
        تحليل نص الخطة وتحويله لـ ParsedPlan
        
        Args:
            plan_text: نص الخطة الاستراتيجية
            
        Returns:
            ParsedPlan object مع Modules و Tasks
        """
        try:
            logger.info("📝 Starting plan parsing...")
            
            # Build prompt
            user_prompt = PLAN_PARSER_USER_PROMPT.format(plan_text=plan_text)
            
            # Call LLM
            result = await self.llm.generate_json(
                prompt=user_prompt,
                system_prompt=PLAN_PARSER_SYSTEM_PROMPT,
                temperature=0.3  # Lower for consistent output
            )
            
            # Convert to entities
            parsed_plan = self._convert_to_parsed_plan(result)
            
            logger.info(f"✅ Plan parsed: {len(parsed_plan.modules)} modules, {parsed_plan.total_tasks} tasks")
            
            return parsed_plan
            
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"❌ Plan parsing failed: {str(e)}")
            raise LLMException(
                message=f"Failed to parse plan: {str(e)}",
                details={"plan_text_length": len(plan_text)}
            )
    
    def _convert_to_parsed_plan(self, llm_result: dict) -> ParsedPlan:
        """تحويل نتيجة الـ LLM إلى ParsedPlan"""
        
        modules: List[Module] = []
        task_counter = 100  # Start task IDs from 100
        
        for mod_idx, mod_data in enumerate(llm_result.get("modules", []), start=1):
            module_id = generate_module_id(mod_idx)
            
            tasks: List[Task] = []
            for task_data in mod_data.get("tasks", []):
                task_counter += 1
                task_id = generate_task_id(task_counter)
                
                # Handle dependencies (convert to task_ids)
                dependencies = []
                for dep in task_data.get("dependencies", []):
                    if isinstance(dep, str):
                        dependencies.append(dep)
                
                task = Task(
                    task_id=task_id,
                    title=task_data.get("title", "Untitled Task"),
                    description=task_data.get("description", ""),
                    required_skill=task_data.get("required_skill"),
                    duration_days=1,  # Will be estimated later
                )
                tasks.append(task)
            
            module = Module(
                module_id=module_id,
                module_name=mod_data.get("module_name", f"Module {mod_idx}"),
                tasks=tasks
            )
            modules.append(module)
        
        return ParsedPlan(
            title=llm_result.get("plan_title", "Untitled Plan"),
            modules=modules
        )


# Service instance
plan_parser_service = PlanParserService()
