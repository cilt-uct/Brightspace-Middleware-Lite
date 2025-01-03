from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class Search(BaseModel):
    value: str
    regex: bool

class Column(BaseModel):
    data: str
    name: str
    searchable: bool
    orderable: bool
    search: Search

class Order(BaseModel):
    column: int
    dir: str

class DataTableRequest(BaseModel):
    draw: int
    columns: List[Column]
    order: List[Order]
    start: int
    length: int
    search: Search
    status: Optional[str] = None

class DataTableResponse(BaseModel):
    draw: int
    data: List[Any]
    counts: List[Any]
    recordsFiltered: int
    recordsTotal: int
