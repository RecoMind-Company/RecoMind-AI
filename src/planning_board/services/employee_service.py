"""
Employee Service
================
Fetch team employees from the .NET backend.
"""

from typing import Any, List, Optional

import httpx
from loguru import logger

from core.config import settings
from core.exceptions import EmployeeServiceException
from models.entities import Employee


class EmployeeService:
    """Service responsible for fetching employees for a company/team."""

    def __init__(
        self,
        url_template: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.url_template = url_template or settings.DOTNET_TEAM_EMPLOYEES_URL_TEMPLATE
        self.token = token if token is not None else settings.DOTNET_API_TOKEN
        self.timeout = float(settings.REQUEST_TIMEOUT)

    async def fetch_employees(self, company_id: str, team_id: str) -> List[Employee]:
        """
        Fetch employees from the .NET API for a specific company and team.
        """
        url = self.url_template.format(company_id=company_id, team_id=team_id)
        headers = self._build_headers()

        try:
            logger.info(f"Fetching employees for company={company_id}, team={team_id}")

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            employees = self._parse_employees(response.json())
            if not employees:
                raise EmployeeServiceException(
                    message="Employee service returned no employees for this team",
                    details={"company_id": company_id, "team_id": team_id},
                )

            logger.info(f"Fetched {len(employees)} employees")
            return employees

        except EmployeeServiceException:
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Employee API HTTP error: {e.response.status_code}")
            raise EmployeeServiceException(
                message=f"Failed to fetch employees: HTTP {e.response.status_code}",
                details={
                    "status_code": e.response.status_code,
                    "company_id": company_id,
                    "team_id": team_id,
                },
            )
        except httpx.RequestError as e:
            logger.error(f"Employee API request error: {str(e)}")
            raise EmployeeServiceException(
                message=f"Failed to connect to employee service: {str(e)}",
                details={"company_id": company_id, "team_id": team_id},
            )
        except Exception as e:
            logger.error(f"Unexpected employee API error: {str(e)}")
            raise EmployeeServiceException(
                message=f"Unexpected error fetching employees: {str(e)}",
                details={"company_id": company_id, "team_id": team_id},
            )

    def _build_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _parse_employees(self, data: Any) -> List[Employee]:
        """Parse common .NET response shapes into Employee entities."""
        employee_items = self._extract_employee_items(data)
        employees: List[Employee] = []

        for item in employee_items:
            # .NET returns plain job-title strings: ["Sales Manager", "Developer", ...]
            if isinstance(item, str):
                job_title = item.strip()
                if not job_title:
                    continue
                slug = job_title.lower().replace(" ", "_").replace("/", "_")
                employees.append(Employee(
                    id=f"role_{slug}",
                    name=job_title,
                    job_title=job_title,
                ))
                continue

            if not isinstance(item, dict):
                continue

            user_id = str(self._first_value(item, "user_id", "userId", "id", "employeeId", "employee_id") or "")
            job_title = str(
                self._first_value(
                    item,
                    "job_title",
                    "jobTitle",
                    "job",
                    "title",
                    "position",
                    "role",
                )
                or ""
            )
            name = str(self._first_value(item, "name", "fullName", "full_name", "employeeName") or "")
            if not name:
                name = job_title

            employee = Employee(
                id=user_id,
                name=name,
                job_title=job_title,
                skills=self._parse_skills(self._first_value(item, "skills", "skillNames")),
                current_workload=int(self._first_value(item, "current_workload", "currentWorkload") or 0),
            )

            if employee.id and employee.job_title:
                employees.append(employee)
            else:
                logger.warning(f"Skipping employee with missing required fields: {item}")

        return employees

    def _extract_employee_items(self, data: Any) -> list[Any]:
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            return []

        for key in ("employees", "teamMembers", "members", "data", "result", "items"):
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = self._extract_employee_items(value)
                if nested:
                    return nested

        return []

    def _first_value(self, data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data and data[key] not in (None, ""):
                return data[key]
        return None

    def _parse_skills(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(skill) for skill in value if skill]
        if isinstance(value, str):
            return [skill.strip() for skill in value.split(",") if skill.strip()]
        return []


def get_employee_service() -> EmployeeService:
    return EmployeeService()


employee_service = get_employee_service()
