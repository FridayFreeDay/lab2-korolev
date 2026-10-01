import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BookCondition(StrEnum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    BAD = "BAD"


class ReservationStatus(StrEnum):
    RENTED = "RENTED"
    RETURNED = "RETURNED"
    EXPIRED = "EXPIRED"


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


class LibraryBookResponse(CamelModel):
    book_uid: uuid.UUID
    name: str
    author: str | None = None
    genre: str | None = None
    condition: BookCondition
    available_count: int


class BookInfo(CamelModel):
    book_uid: uuid.UUID
    name: str
    author: str | None = None
    genre: str | None = None


class PageResponse[T](CamelModel):
    page: int
    page_size: int
    total_elements: int
    items: list[T]


class UserRatingResponse(CamelModel):
    stars: int


class BookReservationResponse(CamelModel):
    reservation_uid: uuid.UUID
    status: ReservationStatus
    start_date: datetime.date
    till_date: datetime.date
    book: BookInfo
    library: LibraryResponse


class TakeBookRequest(CamelModel):
    book_uid: uuid.UUID
    library_uid: uuid.UUID
    till_date: datetime.date


class TakeBookResponse(BookReservationResponse):
    rating: UserRatingResponse


class ReturnBookRequest(CamelModel):
    condition: BookCondition
    date: datetime.date


class ErrorResponse(BaseModel):
    message: str


class ErrorDescription(BaseModel):
    field: str
    error: str


class ValidationErrorResponse(BaseModel):
    message: str
    errors: list[ErrorDescription]
