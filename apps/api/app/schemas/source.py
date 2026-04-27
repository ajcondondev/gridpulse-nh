from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SourceStatus(str, Enum):
    active = "active"
    requires_key = "requires_key"
    manual_import = "manual_import"
    planned = "planned"
    research = "research"
    not_implemented = "not_implemented"
    mock = "mock"


class SourceCategory(str, Enum):
    electricity = "electricity"
    weather = "weather"
    ev = "ev"
    environmental = "environmental"
    resilience = "resilience"
    gis = "gis"
    regulatory = "regulatory"


class Source(BaseModel):
    id: str
    name: str
    description: str
    category: SourceCategory
    status: SourceStatus
    url: Optional[str] = None
    update_frequency: Optional[str] = None
    data_format: Optional[str] = None
    notes: Optional[str] = None
    requires_api_key: Optional[bool] = None
    auth_type: Optional[str] = None
    access_method: Optional[str] = None
    data_geography: Optional[str] = None
    phase_added: Optional[int] = None
    last_verified: Optional[str] = None


class SourceList(BaseModel):
    sources: List[Source]
    total: int
