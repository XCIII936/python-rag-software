"""Common Pydantic schemas."""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100


class PaginatedResponse(BaseModel):
    total: int
    items: List


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
