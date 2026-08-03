"""Custom exception classes for reporting_system."""


class ReportingError(Exception):
    """Base exception class for all reporting_system errors."""

    pass


class DatabaseConnectionError(ReportingError):
    """Raised when connecting to a database (PostgreSQL or SQL Server) fails."""

    pass


class MetadataNotFoundError(ReportingError):
    """Raised when source connection metadata is not found for a given company_id."""

    pass


class QueryExecutionError(ReportingError):
    """Raised when executing a SQL query fails or returns invalid results."""

    pass


class CrewExecutionError(ReportingError):
    """Raised when CrewAI data collection crew fails to produce a valid SQL query."""

    pass


class AnalysisError(ReportingError):
    """Raised when the LangGraph analysis pipeline fails to generate a report."""

    pass
