"""
Pydantic Request Models
=======================
API input models
"""

from pydantic import BaseModel, Field


class ValidationRequest(BaseModel):
    """
    Request model for running the validation pipeline.
    The only required fields are company_id, team_id, and user_request.
    All other data is retrieved automatically from the .NET API.
    """

    company_id: str = Field(
        ...,
        description="Company ID",
        examples=["34293b50-0c58-4111-8fcd-b0127dd250ce"],
    )

    team_id: str = Field(
        ...,
        description="Team ID",
        examples=["0dc1400d-a758-424b-80fb-a8ff89078522"],
    )

    user_request: str = Field(
        ...,
        min_length=10,
        max_length=10000,
        description="Strategic plan or business decision text to validate",
        examples=[
            "Increase company sales by 20% in the next quarter by targeting new customers, "
            "following up with potential customers, conducting product presentations, "
            "negotiating contracts, completing sales, then preparing a final report "
            "showing sales results and performance indicators"
        ],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "34293b50-0c58-4111-8fcd-b0127dd250ce",
                "team_id": "0dc1400d-a758-424b-80fb-a8ff89078522",
                "user_request": "Increase company sales by 20% in the next quarter by targeting new customers, following up with potential customers, conducting product presentations, negotiating contracts, completing sales, then preparing a final report showing sales results and performance indicators",
            }
        }
