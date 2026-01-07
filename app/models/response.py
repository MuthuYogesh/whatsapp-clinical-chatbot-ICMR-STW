from pydantic import BaseModel

class ComplianceResponse(BaseModel):
    compliant: bool
    rationale: str
