import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BookCondition(StrEnum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    BAD = "BAD"


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class LibraryResponse(CamelModel):
    library_uid: uuid.UUID
    name: str
    address: str
    city: str


class BookResponse(CamelModel):
    book_uid: uuid.UUID
    name: str
    author: str | None = None
    genre: str | None = None
    condition: BookCondition


class LibraryBookResponse(CamelModel):
    book_uid: uuid.UUID
    name: str
    author: str | None = None
    genre: str | None = None
    condition: BookCondition
    available_count: int


class PageResponse[T](CamelModel):
    page: int
    page_size: int
    total_elements: int
    items: list[T]


class AvailableCountResponse(CamelModel):
    available_count: int


class ErrorResponse(BaseModel):
    message: str


class ErrorDescription(BaseModel):
    field: str
    error: str


class ValidationErrorResponse(BaseModel):
    message: str
    errors: list[ErrorDescription]
