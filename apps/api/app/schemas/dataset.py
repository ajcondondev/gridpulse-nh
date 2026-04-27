from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Dataset(BaseModel):
    id: str
    source_id: str
    name: str
    fetched_at: Optional[datetime] = None
    row_count: Optional[int] = None
    columns: Optional[List[str]] = None
    raw_path: Optional[str] = None
    cleaned_path: Optional[str] = None
    status: str = "pending"


class DatasetList(BaseModel):
    datasets: List[Dataset]
    total: int
