import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.errors import ReservationAlreadyClosedError, ReservationNotFoundError
from src.models import Reservation
from src.schemas import CreateReservationRequest, ReservationStatus


def _to_timestamp(value: datetime.date) -> datetime.datetime:
    return datetime.datetime.combine(value, datetime.time.min)


def list_reservations(
    session: Session, username: str, status: ReservationStatus | None = None
) -> list[Reservation]:
    statement = select(Reservation).where(Reservation.username == username)
    if status is not None:
        statement = statement.where(Reservation.status == status)
    return list(session.scalars(statement.order_by(Reservation.id)))


def create_reservation(
    session: Session, username: str, request: CreateReservationRequest
) -> Reservation:
    reservation = Reservation(
        reservation_uid=uuid.uuid4(),
        username=username,
        book_uid=request.book_uid,
        library_uid=request.library_uid,
        status=ReservationStatus.RENTED,
        start_date=_to_timestamp(datetime.datetime.now(datetime.UTC).date()),
        till_date=_to_timestamp(request.till_date),
    )
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


def close_reservation(
    session: Session,
    username: str,
    reservation_uid: uuid.UUID,
    return_date: datetime.date,
) -> Reservation:
    """Закрывает бронь, определяя статус по дате возврата.

    Чужая бронь неотличима от несуществующей: иначе по коду ответа
    можно было бы перебором узнать чужие идентификаторы.
    """
    reservation = session.scalar(
        select(Reservation).where(
            Reservation.reservation_uid == reservation_uid,
            Reservation.username == username,
        )
    )
    if reservation is None:
        raise ReservationNotFoundError(reservation_uid)
    if reservation.status != ReservationStatus.RENTED:
        raise ReservationAlreadyClosedError(reservation_uid)

    reservation.status = (
        ReservationStatus.EXPIRED
        if return_date > reservation.till_date.date()
        else ReservationStatus.RETURNED
    )
    session.commit()
    session.refresh(reservation)
    return reservation
