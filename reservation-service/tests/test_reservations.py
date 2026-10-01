import datetime
import uuid

API_PATH = "/api/v1/reservations"
USER = "Test Max"
OTHER_USER = "Other User"
BOOK_UID = "f7cdc58f-2caf-4b15-9727-f89dcc629b27"
LIBRARY_UID = "83575e12-7ce0-48ee-9931-51919ff3c9ee"
TILL_DATE = "2021-10-11"
LATE_DATE = "2021-10-12"
UNKNOWN_UID = "00000000-0000-0000-0000-000000000000"


def _headers(username=USER):
    return {"X-User-Name": username}


def _create(client, username=USER, till_date=TILL_DATE):
    return client.post(
        API_PATH,
        headers=_headers(username),
        json={"bookUid": BOOK_UID, "libraryUid": LIBRARY_UID, "tillDate": till_date},
    )


def _return(client, reservation_uid, date=TILL_DATE, username=USER):
    return client.post(
        f"{API_PATH}/{reservation_uid}/return", headers=_headers(username), json={"date": date}
    )


def test_health_returns_status_up(client):
    response = client.get("/manage/health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_create_returns_rented_reservation(client):
    response = _create(client)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RENTED"
    assert body["tillDate"] == TILL_DATE
    assert uuid.UUID(body["reservationUid"])


def test_start_date_is_today(client):
    response = _create(client)

    assert response.json()["startDate"] == datetime.datetime.now(datetime.UTC).date().isoformat()


def test_list_returns_only_own_reservations(client):
    _create(client)
    _create(client, username=OTHER_USER)

    response = client.get(API_PATH, headers=_headers())

    assert len(response.json()) == 1


def test_list_filters_by_status(client):
    created = _create(client).json()
    _create(client)
    _return(client, created["reservationUid"])

    response = client.get(API_PATH, headers=_headers(), params={"status": "RENTED"})

    assert len(response.json()) == 1


def test_return_in_time_sets_returned(client):
    created = _create(client).json()

    response = _return(client, created["reservationUid"], date=TILL_DATE)

    assert response.status_code == 200
    assert response.json()["status"] == "RETURNED"


def test_return_after_till_date_sets_expired(client):
    created = _create(client).json()

    response = _return(client, created["reservationUid"], date=LATE_DATE)

    assert response.json()["status"] == "EXPIRED"


def test_return_exposes_book_and_library(client):
    created = _create(client).json()

    body = _return(client, created["reservationUid"]).json()

    assert body["bookUid"] == BOOK_UID
    assert body["libraryUid"] == LIBRARY_UID


def test_return_of_foreign_reservation_returns_404(client):
    created = _create(client).json()

    response = _return(client, created["reservationUid"], username=OTHER_USER)

    assert response.status_code == 404


def test_return_unknown_reservation_returns_404(client):
    response = _return(client, UNKNOWN_UID)

    assert response.status_code == 404


def test_second_return_returns_409(client):
    created = _create(client).json()
    _return(client, created["reservationUid"])

    response = _return(client, created["reservationUid"])

    assert response.status_code == 409


def test_create_without_user_header_returns_400(client):
    response = client.post(
        API_PATH, json={"bookUid": BOOK_UID, "libraryUid": LIBRARY_UID, "tillDate": TILL_DATE}
    )

    assert response.status_code == 400
