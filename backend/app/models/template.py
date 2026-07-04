from pydantic import BaseModel
from typing import List, Optional


class TemplateMeta(BaseModel):
    id: str
    name: str
    filename: str
    sections: List[str]