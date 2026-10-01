def _take_path(catalog, book_key="available_book_uid"):
    return f"/api/v1/libraries/{catalog['library_uid']}/books/{catalog[book_key]}/take"


def _return_path(catalog, book_key="available_book_uid"):
    return f"/api/v1/libraries/{catalog['library_uid']}/books/{catalog[book_key]}/return"


def test_take_decrements_available_count(client, catalog):
    response = client.post(_take_path(catalog))

    assert response.status_code == 200
    assert response.json()["availableCount"] == 0


def test_take_last_copy_twice_returns_409(client, catalog):
    client.post(_take_path(catalog))

    response = client.post(_take_path(catalog))

    assert response.status_code == 409
    assert "message" in response.json()


def test_take_unavailable_book_returns_409(client, catalog):
    response = client.post(_take_path(catalog, "taken_book_uid"))

    assert response.status_code == 409


def test_return_increments_available_count(client, catalog):
    client.post(_take_path(catalog))

    response = client.post(_return_path(catalog))

    assert response.status_code == 200
    assert response.json()["availableCount"] == 1
