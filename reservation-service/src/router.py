import uuid

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from src import repository
from src.database import get_db
from src.schemas import (
    CreateReservationRequest,
    ErrorResponse,
    ReservationResponse,
    ReservationStatus,
    ReturnReservationRequest,
)

API_PREFIX = "/api/v1/reservations"
USER_NAME_HEADER = "X-User-Name"

router = APIRouter(prefix=API_PREFIX, tags=["Reservation"])


@router.get("", response_model=list[ReservationResponse])
def list_reservations(
    status_filter: ReservationStatus | None = Query(None, alias="status"),
    username: str = Header(alias=USER_NAME_HEADER),
    session: Session = Depends(get_db),
) -> list[ReservationResponse]:
    reservations = repository.list_reservations(session, username, status_filter)
    return [ReservationResponse.model_validate(item) for item in reservations]


@router.post("", response_model=ReservationResponse)
def create_reservation(
    request: CreateReservationRequest,
    username: str = Header(alias=USER_NAME_HEADER),
    session: Session = Depends(get_db),
) -> ReservationResponse:
    return ReservationResponse.model_validate(
        repository.create_reservation(session, username, request)
    )


@router.post(
    "/{reservation_uid}/return",
    response_model=ReservationResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
def return_reservation(
    reservation_uid: uuid.UUID,
    request: ReturnReservationRequest,
    username: str = Header(alias=USER_NAME_HEADER),
    session: Session = Depends(get_db),
) -> ReservationResponse:
    return ReservationResponse.model_validate(
        repository.close_reservation(session, username, reservation_uid, request.date)
    )
