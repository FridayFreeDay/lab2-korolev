import httpx
import pytest
from fastapi.testclient import TestClient

from src import clients
from src.config import settings
from src.main import app


class Upstream:
    """Заглушка трёх сервисов: ответы задаются по паре (метод, путь).

    Подменяется транспорт httpx, а не функции клиента, — так тесты проверяют
    и сборку URL, и параметры запроса, а не только ветвления оркестрации.
    """

    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], httpx.Response] = {}
        self.requests: list[httpx.Request] = []

    def on(self, method: str, path: str, json=None, status_code: int = 200) -> None:
        self.routes[(method, path)] = httpx.Response(status_code, json=json)

    def fail(self, method: str, path: str) -> None:
        self.routes[(method, path)] = httpx.ConnectError("upstream is down")

    def called(self, method: str, path: str) -> int:
        return sum(1 for r in self.requests if r.method == method and r.url.path == path)

    def request(self, method: str, path: str) -> httpx.Request:
        return next(r for r in self.requests if r.method == method and r.url.path == path)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        route = self.routes.get((request.method, request.url.path))
        if route is None:
            return httpx.Response(404, json={"message": "not found"})
        if isinstance(route, Exception):
            raise route
        return route


@pytest.fixture()
def upstream():
    return Upstream()


@pytest.fixture()
def client(upstream, monkeypatch):
    transport = httpx.MockTransport(upstream._handle)
    monkeypatch.setattr(clients, "_client", httpx.AsyncClient(transport=transport))
    return TestClient(app)


@pytest.fixture()
def urls():
    return {
        "library": settings.library_service_url,
        "reservation": settings.reservation_service_url,
        "rating": settings.rating_service_url,
    }
