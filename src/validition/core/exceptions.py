"""
Custom Exceptions
=================
Custom exceptions for Validation feature
"""

from typing import Any, Dict, Optional


class ValidationException(Exception):
    """Base exception for Validation feature"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class LLMException(ValidationException):
    """Exception for LLM-related errors"""

    def __init__(
        self,
        message: str = "LLM processing failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=502, details=details)


class AuthenticationException(ValidationException):
    """Exception for authentication errors with external API"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=401, details=details)


class CompanyServiceException(ValidationException):
    """Exception for company info retrieval errors"""

    def __init__(
        self,
        message: str = "Failed to fetch company information",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=503, details=details)


class ReportsServiceException(ValidationException):
    """Exception for reports retrieval errors"""

    def __init__(
        self,
        message: str = "Failed to fetch reports",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=503, details=details)


class StrategyStructuringException(ValidationException):
    """Exception for strategy structuring errors"""

    def __init__(
        self,
        message: str = "Strategy structuring failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, details=details)


class PrecedentEngineException(ValidationException):
    """Exception for precedent engine errors"""

    def __init__(
        self,
        message: str = "Precedent engine failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, details=details)


class ResourceSimulationException(ValidationException):
    """Exception for resource simulation errors"""

    def __init__(
        self,
        message: str = "Resource simulation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=500, details=details)


class TimeoutException(ValidationException):
    """Exception for timeout errors"""

    def __init__(
        self,
        message: str = "Request timeout",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, status_code=504, details=details)
