from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class SourceStatus(str, Enum):
    active = "active"
    unavailable = "unavailable"
    mock = "mock"
    planned = "planned"


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


class SourceList(BaseModel):
    sources: List[Source]
    total: int
