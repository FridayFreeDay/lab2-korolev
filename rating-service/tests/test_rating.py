from src.repository import DEFAULT_STARS, MAX_STARS, MIN_STARS

API_PATH = "/api/v1/rating"
USER = "Test Max"
OTHER_USER = "Other User"


def _headers(username=USER):
    return {"X-User-Name": username}


def _get_stars(client, username=USER):
    return client.get(API_PATH, headers=_headers(username)).json()["stars"]


def _patch(client, delta, username=USER):
    return client.patch(API_PATH, headers=_headers(username), json={"delta": delta})


def test_health_returns_status_up(client):
    response = client.get("/manage/health")

    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_unknown_user_gets_default_rating(client):
    response = client.get(API_PATH, headers=_headers())

    assert response.status_code == 200
    assert response.json() == {"stars": DEFAULT_STARS}


def test_repeated_get_does_not_create_second_record(client):
    _get_stars(client)
    _patch(client, 1)

    assert _get_stars(client) == DEFAULT_STARS + 1


def test_patch_increases_stars(client):
    response = _patch(client, 1)

    assert response.status_code == 200
    assert response.json()["stars"] == DEFAULT_STARS + 1


def test_patch_decreases_stars(client):
    response = _patch(client, -10)

    assert response.json()["stars"] == DEFAULT_STARS - 10


def test_stars_never_exceed_maximum(client):
    _patch(client, MAX_STARS)

    assert _get_stars(client) == MAX_STARS


def test_stars_never_drop_below_minimum(client):
    _patch(client, -MAX_STARS)

    assert _get_stars(client) == MIN_STARS


def test_ratings_are_isolated_per_user(client):
    _patch(client, 1)

    assert _get_stars(client, OTHER_USER) == DEFAULT_STARS


def test_request_without_user_header_returns_400(client):
    response = client.get(API_PATH)

    assert response.status_code == 400
    assert response.json()["errors"][0]["field"] == "header.X-User-Name"
