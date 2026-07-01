"""
Core Module
============
Re-exports settings and exceptions
"""

from core.config import settings
from core.exceptions import (
    ValidationException,
    LLMException,
    AuthenticationException,
    CompanyServiceException,
    ReportsServiceException,
    StrategyStructuringException,
    PrecedentEngineException,
    ResourceSimulationException,
    TimeoutException,
)

__all__ = [
    "settings",
    "ValidationException",
    "LLMException",
    "AuthenticationException",
    "CompanyServiceException",
    "ReportsServiceException",
    "StrategyStructuringException",
    "PrecedentEngineException",
    "ResourceSimulationException",
    "TimeoutException",
]
