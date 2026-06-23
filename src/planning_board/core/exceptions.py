"""
Custom Exceptions
=================
استثناءات مخصصة للـ Planning Board
"""

from typing import Any, Dict, Optional


class PlanningBoardException(Exception):
    """Base exception for Planning Board"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class LLMException(PlanningBoardException):
    """Exception for LLM-related errors"""
    
    def __init__(
        self,
        message: str = "LLM processing failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=502, details=details)


class EmployeeServiceException(PlanningBoardException):
    """Exception for Employee Service errors"""
    
    def __init__(
        self,
        message: str = "Failed to fetch employees",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=503, details=details)


class ValidationException(PlanningBoardException):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=422, details=details)


class TaskAssignmentException(PlanningBoardException):
    """Exception for task assignment errors"""
    
    def __init__(
        self,
        message: str = "Task assignment failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=500, details=details)


class TimeoutException(PlanningBoardException):
    """Exception for timeout errors"""
    
    def __init__(
        self,
        message: str = "Request timeout",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, status_code=504, details=details)
