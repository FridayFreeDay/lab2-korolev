import uuid

LIBRARIES_PATH = "/api/v1/libraries"
UNKNOWN_UID = uuid.UUID("00000000-0000-0000-0000-000000000000")


def test_health_returns_status_up(client):
    response = client.get("/manage/health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_list_libraries_returns_page_for_city(client, catalog):
    response = client.get(LIBRARIES_PATH, params={"city": "Москва", "page": 1, "size": 10})

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["pageSize"] == 10
    assert body["totalElements"] == 1
    assert body["items"][0]["libraryUid"] == str(catalog["library_uid"])


def test_list_libraries_filters_out_other_cities(client, catalog):
    response = client.get(LIBRARIES_PATH, params={"city": "Казань"})

    assert response.json()["totalElements"] == 1
    assert response.json()["items"][0]["libraryUid"] == str(catalog["other_library_uid"])


def test_first_page_is_numbered_one(client, catalog):
    first = client.get(LIBRARIES_PATH, params={"city": "Москва", "page": 1, "size": 10})
    second = client.get(LIBRARIES_PATH, params={"city": "Москва", "page": 2, "size": 10})

    assert first.json()["items"] != []
    assert second.json()["items"] == []


def test_get_library_by_uid(client, catalog):
    response = client.get(f"{LIBRARIES_PATH}/{catalog['library_uid']}")

    assert response.status_code == 200
    assert response.json()["city"] == "Москва"


def test_get_unknown_library_returns_404(client, catalog):
    response = client.get(f"{LIBRARIES_PATH}/{UNKNOWN_UID}")

    assert response.status_code == 404
    assert "message" in response.json()


def test_lookup_libraries_returns_requested_uids(client, catalog):
    response = client.get(
        "/api/v1/lookup/libraries",
        params={"uids": f"{catalog['library_uid']},{catalog['other_library_uid']}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
