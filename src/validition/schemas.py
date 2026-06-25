from pydantic import BaseModel
from typing import List, Dict, Optional


class PrimaryActionDetails(BaseModel):
    location: str
    channel: str


class PrimaryAction(BaseModel):
    action_type: str
    details: PrimaryActionDetails


class PrecedentEngineInput(BaseModel):
    strategy_type: str
    decision_category: str
    primary_action: PrimaryAction


class HiringDetails(BaseModel):
    department: str
    scale: str
    

class ActionItem(BaseModel):
    action_type: str
    details: Optional[Dict] = None



class ResourceRequirements(BaseModel):
    financial: List[str]
    human: List[str]
    operational: List[str]


class ResourceSimulatorInput(BaseModel):
    all_actions: List[ActionItem]
    resource_requirements: ResourceRequirements
    time_horizon: str


class TargetMarket(BaseModel):
    location: str


class MarketTrendEngineInput(BaseModel):
    strategy_type: str
    target_market: TargetMarket


class StrategyOutput(BaseModel):
    precedent_engine_input: PrecedentEngineInput
    resource_simulator_input: ResourceSimulatorInput
    market_trend_engine_input: MarketTrendEngineInput