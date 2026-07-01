"""
Services Module
===============
Re-exports all agent services
"""

from services.strategy_structuring import StrategyStructuringService, strategy_structuring_service
from services.precedent_engine import PrecedentEngineService, precedent_engine_service
from services.precedent_engine import PrecedentAnalyzer, precedent_analyzer
from services.resource_simulator import ResourceSimulatorService, resource_simulator_service
from services.market_trend_engine import MarketTrendEngineService, market_trend_engine_service
from services.report_generation import ReportGenerationService, report_generation_service
from services.validation_pipeline import ValidationPipelineService, validation_pipeline_service

__all__ = [
    "StrategyStructuringService",
    "strategy_structuring_service",
    "PrecedentEngineService",
    "precedent_engine_service",
    "PrecedentAnalyzer",
    "precedent_analyzer",
    "ResourceSimulatorService",
    "resource_simulator_service",
    "MarketTrendEngineService",
    "market_trend_engine_service",
    "ReportGenerationService",
    "report_generation_service",
    "ValidationPipelineService",
    "validation_pipeline_service",
]
