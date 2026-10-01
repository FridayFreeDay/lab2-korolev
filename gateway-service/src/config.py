from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_PORT = 8080
DEFAULT_LIBRARY_SERVICE_URL = "http://localhost:8060"
DEFAULT_RESERVATION_SERVICE_URL = "http://localhost:8070"
DEFAULT_RATING_SERVICE_URL = "http://localhost:8050"

CONNECT_TIMEOUT_SECONDS = 2.0
READ_TIMEOUT_SECONDS = 5.0
POOL_TIMEOUT_SECONDS = 2.0
MAX_CONNECTIONS = 100
MAX_KEEPALIVE_CONNECTIONS = 20


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    port: int = DEFAULT_PORT
    library_service_url: str = DEFAULT_LIBRARY_SERVICE_URL
    reservation_service_url: str = DEFAULT_RESERVATION_SERVICE_URL
    rating_service_url: str = DEFAULT_RATING_SERVICE_URL


settings = Settings()
