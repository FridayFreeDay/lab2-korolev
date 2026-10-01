-- Отдельные базы под unit-тесты: pytest чистит таблицы через TRUNCATE
-- и не должен трогать данные, по которым потом бежит newman.
CREATE DATABASE libraries_test;
CREATE DATABASE reservations_test;
CREATE DATABASE ratings_test;

GRANT ALL PRIVILEGES ON DATABASE libraries_test TO program;
GRANT ALL PRIVILEGES ON DATABASE reservations_test TO program;
GRANT ALL PRIVILEGES ON DATABASE ratings_test TO program;
