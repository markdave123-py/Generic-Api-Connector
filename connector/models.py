from typing import List, Optional

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(..., pattern=r"(?i)^bearer$")
    expires_in: int  # seconds


class Item(BaseModel):
    id: int
    name: str
    value: float


class ItemPage(BaseModel):
    items: List[Item]
    page: int
    total_pages: int
    next_page: Optional[int] = None
