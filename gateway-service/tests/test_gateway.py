import datetime

USER = "Test Max"
HEADERS = {"X-User-Name": USER}
BOOK_UID = "f7cdc58f-2caf-4b15-9727-f89dcc629b27"
LIBRARY_UID = "83575e12-7ce0-48ee-9931-51919ff3c9ee"
RESERVATION_UID = "f464ca3a-fcf7-4e3f-86f0-76c7bba96f72"
TILL_DATE = "2021-10-11"

LIBRARY = {
    "libraryUid": LIBRARY_UID,
    "name": "Библиотека имени 7 Непьющих",
    "address": "2-я Бауманская ул., д.5, стр.1",
    "city": "Москва",
}
BOOK = {
    "bookUid": BOOK_UID,
    "name": "Краткий курс C++ в 7 томах",
    "author": "Бьерн Страуструп",
    "genre": "Научная фантастика",
    "condition": "EXCELLENT",
}
RESERVATION = {
    "reservationUid": RESERVATION_UID,
    "username": USER,
    "bookUid": BOOK_UID,
    "libraryUid": LIBRARY_UID,
    "status": "RENTED",
    "startDate": "2021-10-09",
    "tillDate": TILL_DATE,
}

LIBRARY_PATH = f"/api/v1/libraries/{LIBRARY_UID}"
BOOK_PATH = f"/api/v1/books/{BOOK_UID}"
RESERVATIONS_PATH = "/api/v1/reservations"
RATING_PATH = "/api/v1/rating"
TAKE_PATH = f"{LIBRARY_PATH}/books/{BOOK_UID}/take"
RETURN_BOOK_PATH = f"{LIBRARY_PATH}/books/{BOOK_UID}/return"
CLOSE_PATH = f"{RESERVATIONS_PATH}/{RESERVATION_UID}/return"


def _arrange_rent(upstream, stars=75, rented=()):
    upstream.on("GET", LIBRARY_PATH, LIBRARY)
    upstream.on("GET", BOOK_PATH, BOOK)
    upstream.on("GET", RATING_PATH, {"stars": stars})
    upstream.on("GET", RESERVATIONS_PATH, list(rented))
    upstream.on("POST", TAKE_PATH, {"availableCount": 0})
    upstream.on("POST", RESERVATIONS_PATH, RESERVATION)


def _rent(client):
    return client.post(
        RESERVATIONS_PATH,
        headers=HEADERS,
        json={"bookUid": BOOK_UID, "libraryUid": LIBRARY_UID, "tillDate": TILL_DATE},
    )


def _arrange_return(upstream, status="RETURNED", condition="EXCELLENT"):
    upstream.on("POST", CLOSE_PATH, {**RESERVATION, "status": status})
    upstream.on("POST", RETURN_BOOK_PATH, {"availableCount": 1})
    upstream.on("GET", BOOK_PATH, {**BOOK, "condition": condition})
    upstream.on("PATCH", RATING_PATH, {"stars": 75})


def _return(client, condition="EXCELLENT"):
    return client.post(
        CLOSE_PATH, headers=HEADERS, json={"condition": condition, "date": TILL_DATE}
    )


def test_health_returns_status_up(client):
    response = client.get("/manage/health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_list_libraries_passes_query_to_library_service(client, upstream):
    upstream.on("GET", "/api/v1/libraries", {"page": 1, "pageSize": 10, "totalElements": 1, "items": [LIBRARY]})

    response = client.get("/api/v1/libraries", params={"city": "Москва", "page": 1, "size": 10})

    assert response.status_code == 200
    assert response.json()["items"][0]["libraryUid"] == LIBRARY_UID
    assert upstream.request("GET", "/api/v1/libraries").url.params["city"] == "Москва"


def test_list_books_forwards_show_all_flag(client, upstream):
    upstream.on("GET", f"{LIBRARY_PATH}/books", {"page": 1, "pageSize": 10, "totalElements": 0, "items": []})

    client.get(f"/api/v1/libraries/{LIBRARY_UID}/books", params={"showAll": True})

    assert upstream.request("GET", f"{LIBRARY_PATH}/books").url.params["showAll"] == "true"


def test_rent_returns_reservation_with_rating(client, upstream):
    _arrange_rent(upstream)

    response = _rent(client)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "RENTED"
    assert body["tillDate"] == TILL_DATE
    assert body["book"]["bookUid"] == BOOK_UID
    assert body["library"]["city"] == "Москва"
    assert body["rating"]["stars"] == 75


def test_rent_is_rejected_when_rented_count_reaches_stars(client, upstream):
    _arrange_rent(upstream, stars=1, rented=[RESERVATION])

    response = _rent(client)

    assert response.status_code == 409
    assert upstream.called("POST", TAKE_PATH) == 0
    assert upstream.called("POST", RESERVATIONS_PATH) == 0


def test_rent_without_available_copies_returns_409(client, upstream):
    _arrange_rent(upstream)
    upstream.on("POST", TAKE_PATH, {"message": "not available"}, status_code=409)

    response = _rent(client)

    assert response.status_code == 409
    assert upstream.called("POST", RESERVATIONS_PATH) == 0


def test_rent_with_unknown_library_returns_404(client, upstream):
    _arrange_rent(upstream)
    upstream.on("GET", LIBRARY_PATH, {"message": "not found"}, status_code=404)

    response = _rent(client)

    assert response.status_code == 404


def test_unavailable_service_returns_503(client, upstream):
    _arrange_rent(upstream)
    upstream.fail("GET", RATING_PATH)

    response = _rent(client)

    assert response.status_code == 503


def test_list_reservations_enriches_with_book_and_library(client, upstream):
    upstream.on("GET", RESERVATIONS_PATH, [RESERVATION])
    upstream.on("GET", "/api/v1/lookup/books", [BOOK])
    upstream.on("GET", "/api/v1/lookup/libraries", [LIBRARY])

    response = client.get(RESERVATIONS_PATH, headers=HEADERS)

    assert response.status_code == 200
    item = response.json()[0]
    assert item["book"]["name"] == BOOK["name"]
    assert item["library"]["name"] == LIBRARY["name"]


def test_return_in_time_and_in_condition_adds_one_star(client, upstream):
    _arrange_return(upstream)

    response = _return(client)

    assert response.status_code == 204
    assert upstream.request("PATCH", RATING_PATH).read() == b'{"delta":1}'


def test_expired_return_costs_ten_stars(client, upstream):
    _arrange_return(upstream, status="EXPIRED")

    _return(client)

    assert upstream.request("PATCH", RATING_PATH).read() == b'{"delta":-10}'


def test_damaged_book_costs_ten_stars(client, upstream):
    _arrange_return(upstream)

    _return(client, condition="BAD")

    assert upstream.request("PATCH", RATING_PATH).read() == b'{"delta":-10}'


def test_expired_and_damaged_return_costs_twenty_stars(client, upstream):
    _arrange_return(upstream, status="EXPIRED")

    _return(client, condition="GOOD")

    assert upstream.request("PATCH", RATING_PATH).read() == b'{"delta":-20}'


def test_rating_is_taken_from_rating_service(client, upstream):
    upstream.on("GET", RATING_PATH, {"stars": 42})

    response = client.get(RATING_PATH, headers=HEADERS)

    assert response.status_code == 200
    assert response.json() == {"stars": 42}


def test_request_without_user_header_returns_400(client, upstream):
    response = client.get(RATING_PATH)

    assert response.status_code == 400


def test_cyrillic_username_is_forwarded(client, upstream):
    upstream.on("GET", RATING_PATH, {"stars": 75})

    response = client.get(RATING_PATH, headers={"X-User-Name": "Иван Петров".encode()})

    assert response.status_code == 200
    forwarded = upstream.request("GET", RATING_PATH).headers
    assert forwarded["X-User-Name"] == "Иван Петров"
