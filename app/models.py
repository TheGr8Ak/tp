from pydantic import BaseModel
from typing import Optional

class Lead(BaseModel):
    company_name: Optional[str] = None
    industry: Optional[str] = None
    location: Optional[str] = None
    project_description: str
    source_platform: str
    source_link: str
    public_contact_info: Optional[str] = None
    website: Optional[str] = None
    date_found: str
    priority_score: int
