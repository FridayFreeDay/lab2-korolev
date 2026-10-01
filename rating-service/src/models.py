from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base

MAX_USERNAME_LENGTH = 80
MIN_STARS = 0
MAX_STARS = 100


class Rating(Base):
    __tablename__ = "rating"
    __table_args__ = (
        CheckConstraint(f"stars BETWEEN {MIN_STARS} AND {MAX_STARS}", name="rating_stars_range"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(MAX_USERNAME_LENGTH), nullable=False, index=True)
    stars: Mapped[int] = mapped_column(Integer, nullable=False)
