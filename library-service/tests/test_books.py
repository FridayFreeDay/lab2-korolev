import uuid

UNKNOWN_UID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def _books_path(library_uid):
    return f"/api/v1/libraries/{library_uid}/books"


def test_list_books_hides_unavailable_by_default(client, catalog):
    response = client.get(_books_path(catalog["library_uid"]))

    assert response.status_code == 200
    body = response.json()
    assert body["totalElements"] == 1
    assert body["items"][0]["bookUid"] == str(catalog["available_book_uid"])


def test_list_books_shows_unavailable_when_flag_set(client, catalog):
    response = client.get(_books_path(catalog["library_uid"]), params={"showAll": True})

    assert response.json()["totalElements"] == 2


def test_list_books_returns_available_count(client, catalog):
    response = client.get(_books_path(catalog["library_uid"]))

    assert response.json()["items"][0]["availableCount"] == 1


def test_list_books_of_unknown_library_returns_404(client, catalog):
    response = client.get(_books_path(UNKNOWN_UID))

    assert response.status_code == 404


def test_get_book_returns_condition(client, catalog):
    response = client.get(f"/api/v1/books/{catalog['available_book_uid']}")

    assert response.status_code == 200
    assert response.json()["condition"] == "EXCELLENT"


def test_get_unknown_book_returns_404(client, catalog):
    response = client.get(f"/api/v1/books/{UNKNOWN_UID}")

    assert response.status_code == 404


def test_lookup_books_returns_requested_uids(client, catalog):
    response = client.get(
        "/api/v1/lookup/books",
        params={"uids": f"{catalog['available_book_uid']},{catalog['taken_book_uid']}"},
    )

    assert len(response.json()) == 2
