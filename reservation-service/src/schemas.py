import datetime
import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


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


class CreateReservationRequest(CamelModel):
    book_uid: uuid.UUID
    library_uid: uuid.UUID
    till_date: datetime.date


class ReturnReservationRequest(CamelModel):
    date: datetime.date


class ReservationResponse(CamelModel):
    reservation_uid: uuid.UUID
    username: str
    book_uid: uuid.UUID
    library_uid: uuid.UUID
    status: ReservationStatus
    start_date: datetime.date
    till_date: datetime.date

    @field_validator("start_date", "till_date", mode="before")
    @classmethod
    def _drop_time(cls, value: object) -> object:
        """БД хранит даты как TIMESTAMP, наружу контракт отдаёт только день."""
        return value.date() if isinstance(value, datetime.datetime) else value


class ErrorResponse(BaseModel):
    message: str


class ErrorDescription(BaseModel):
    field: str
    error: str


class ValidationErrorResponse(BaseModel):
    message: str
    errors: list[ErrorDescription]
