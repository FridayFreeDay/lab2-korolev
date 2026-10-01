from sqlalchemy import select, text
from sqlalchemy.orm import Session

from src.models import Rating

DEFAULT_STARS = 75
MIN_STARS = 1
MAX_STARS = 100
USERNAME_LOCK_SQL = text("SELECT pg_advisory_xact_lock(hashtext(:username))")


def get_or_create_rating(session: Session, username: str) -> Rating:
    """Возвращает рейтинг пользователя, заводя запись с дефолтом при первом обращении.

    Блокировка по имени нужна потому, что username в схеме не уникален:
    без неё два одновременных запроса нового пользователя создадут две строки.
    """
    session.execute(USERNAME_LOCK_SQL, {"username": username})
    rating = session.scalar(
        select(Rating).where(Rating.username == username).order_by(Rating.id).limit(1)
    )
    if rating is None:
        rating = Rating(username=username, stars=DEFAULT_STARS)
        session.add(rating)
    session.commit()
    session.refresh(rating)
    return rating


def update_stars(session: Session, username: str, delta: int) -> Rating:
    rating = get_or_create_rating(session, username)
    rating.stars = min(MAX_STARS, max(MIN_STARS, rating.stars + delta))
    session.commit()
    session.refresh(rating)
    return rating
