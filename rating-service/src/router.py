from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from src import repository
from src.database import get_db
from src.schemas import RatingResponse, UpdateRatingRequest

API_PREFIX = "/api/v1/rating"
USER_NAME_HEADER = "X-User-Name"

router = APIRouter(prefix=API_PREFIX, tags=["Rating"])


@router.get("", response_model=RatingResponse, summary="Get user rating")
def get_rating(
    username: str = Header(alias=USER_NAME_HEADER),
    session: Session = Depends(get_db),
) -> RatingResponse:
    return RatingResponse.model_validate(repository.get_or_create_rating(session, username))


@router.patch("", response_model=RatingResponse, summary="Change user rating")
def update_rating(
    request: UpdateRatingRequest,
    username: str = Header(alias=USER_NAME_HEADER),
    session: Session = Depends(get_db),
) -> RatingResponse:
    return RatingResponse.model_validate(
        repository.update_stars(session, username, request.delta)
    )
