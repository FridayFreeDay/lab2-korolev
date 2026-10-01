from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class RatingResponse(CamelModel):
    stars: int


class UpdateRatingRequest(CamelModel):
    delta: int


class ErrorResponse(BaseModel):
    message: str


class ErrorDescription(BaseModel):
    field: str
    error: str


class ValidationErrorResponse(BaseModel):
    message: str
    errors: list[ErrorDescription]
