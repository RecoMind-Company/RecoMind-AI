"""
Employee Service
================
خدمة جلب بيانات الموظفين من .NET API
"""

from typing import List, Optional
import httpx
from loguru import logger

from core.config import settings
from core.exceptions import EmployeeServiceException
from models.entities import Employee


class EmployeeService:
    """خدمة الموظفين"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        token: Optional[str] = None
    ):
        self.base_url = base_url or settings.DOTNET_API_BASE_URL
        self.token = token or settings.DOTNET_API_TOKEN
        self.timeout = 30.0
    
    async def fetch_employees(self, team_name: str) -> List[Employee]:
        """
        جلب الموظفين من .NET API
        
        Args:
            team_name: اسم الفريق
            
        Returns:
            قائمة الموظفين
        """
        try:
            url = f"{self.base_url}/api/employees"
            headers = {"Authorization": f"Bearer {self.token}"}
            params = {"team_name": team_name}
            
            logger.info(f"📡 Fetching employees for team: {team_name}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                employees = self._parse_employees(data)
                
                logger.info(f"✅ Fetched {len(employees)} employees")
                return employees
                
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ HTTP error: {e.response.status_code}")
            raise EmployeeServiceException(
                message=f"Failed to fetch employees: HTTP {e.response.status_code}",
                details={"status_code": e.response.status_code, "team_name": team_name}
            )
        except httpx.RequestError as e:
            logger.error(f"❌ Request error: {str(e)}")
            raise EmployeeServiceException(
                message=f"Failed to connect to employee service: {str(e)}",
                details={"team_name": team_name}
            )
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            raise EmployeeServiceException(
                message=f"Unexpected error fetching employees: {str(e)}",
                details={"team_name": team_name}
            )
    
    def _parse_employees(self, data: dict) -> List[Employee]:
        """تحويل الـ Response لـ Employee objects"""
        employees = []
        
        for emp_data in data.get("employees", []):
            employee = Employee(
                id=emp_data.get("id", ""),
                name=emp_data.get("name", ""),
                job_title=emp_data.get("job_title", ""),
                skills=emp_data.get("skills", [])
            )
            employees.append(employee)
        
        return employees


class MockEmployeeService(EmployeeService):
    """
    Mock Employee Service للتطوير والاختبار
    يُستخدم عندما .NET API غير متاح
    """
    
    # Mock data
    MOCK_TEAMS = {
        "Marketing": [
            Employee(id="emp_01", name="أحمد", job_title="Marketing Specialist"),
            Employee(id="emp_02", name="سارة", job_title="Content Writer"),
            Employee(id="emp_03", name="محمد", job_title="Social Media Manager"),
        ],
        "Engineering": [
            Employee(id="emp_04", name="علي", job_title="Software Engineer"),
            Employee(id="emp_05", name="فاطمة", job_title="Frontend Developer"),
            Employee(id="emp_06", name="خالد", job_title="Backend Developer"),
        ],
        "Sales": [
            Employee(id="emp_07", name="نورا", job_title="Sales Representative"),
            Employee(id="emp_08", name="يوسف", job_title="Account Manager"),
            Employee(id="emp_09", name="ليلى", job_title="Business Development"),
        ],
        "Design": [
            Employee(id="emp_10", name="رنا", job_title="Graphic Designer"),
            Employee(id="emp_11", name="عمر", job_title="UI/UX Designer"),
            Employee(id="emp_12", name="دينا", job_title="Video Editor"),
        ],
        "HR": [
            Employee(id="emp_13", name="مريم", job_title="HR Specialist"),
            Employee(id="emp_14", name="كريم", job_title="Recruiter"),
        ],
    }
    
    async def fetch_employees(self, team_name: str) -> List[Employee]:
        """
        إرجاع بيانات Mock للموظفين
        """
        logger.info(f"🧪 [MOCK] Fetching employees for team: {team_name}")
        
        # Try exact match first
        if team_name in self.MOCK_TEAMS:
            employees = self.MOCK_TEAMS[team_name]
            logger.info(f"✅ [MOCK] Found {len(employees)} employees")
            return employees
        
        # Try case-insensitive match
        for key, employees in self.MOCK_TEAMS.items():
            if key.lower() == team_name.lower():
                logger.info(f"✅ [MOCK] Found {len(employees)} employees")
                return employees
        
        # Return default team
        logger.warning(f"⚠️ [MOCK] Team '{team_name}' not found, returning Marketing team")
        return self.MOCK_TEAMS["Marketing"]


def get_employee_service(use_mock: bool = None) -> EmployeeService:
    """
    Factory function للحصول على Employee Service
    
    Args:
        use_mock: استخدام Mock Service (None = حسب البيئة)
        
    Returns:
        EmployeeService or MockEmployeeService
    """
    if use_mock is None:
        # Use mock in development if no token configured
        use_mock = settings.is_development and not settings.DOTNET_API_TOKEN
    
    if use_mock:
        logger.info("🧪 Using MockEmployeeService")
        return MockEmployeeService()
    
    logger.info("📡 Using EmployeeService")
    return EmployeeService()


# Default service instance
employee_service = get_employee_service()
