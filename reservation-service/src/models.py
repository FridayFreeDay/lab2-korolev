import datetime
import uuid

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

MAX_USERNAME_LENGTH = 80
MAX_STATUS_LENGTH = 20


class Reservation(Base):
    __tablename__ = "reservation"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RENTED', 'RETURNED', 'EXPIRED')", name="reservation_status_values"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reservation_uid: Mapped[uuid.UUID] = mapped_column(Uuid, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(MAX_USERNAME_LENGTH), nullable=False, index=True)
    book_uid: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    library_uid: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(MAX_STATUS_LENGTH), nullable=False)
    start_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    till_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
