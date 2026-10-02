from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from src import repository
from src.database import get_db
from src.schemas import RatingResponse, UpdateRatingRequest

API_PREFIX = "/api/v1/rating"
USER_NAME_HEADER = "X-User-Name"

router = APIRouter(prefix=API_PREFIX, tags=["Rating"])


def user_name(raw: str = Header(alias=USER_NAME_HEADER)) -> str:
    """Возвращает имя в UTF-8: заголовки приходят декодированными как latin-1."""
    try:
        return raw.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return raw


@router.get("", response_model=RatingResponse, summary="Get user rating")
def get_rating(
    username: str = Depends(user_name),
    session: Session = Depends(get_db),
) -> RatingResponse:
    return RatingResponse.model_validate(repository.get_or_create_rating(session, username))


@router.patch("", response_model=RatingResponse, summary="Change user rating")
def update_rating(
    request: UpdateRatingRequest,
    username: str = Depends(user_name),
    session: Session = Depends(get_db),
) -> RatingResponse:
    return RatingResponse.model_validate(
        repository.update_stars(session, username, request.delta)
    )
