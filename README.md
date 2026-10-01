# Лабораторная работа №2 — Library System (вариант v4)

Система из четырёх сервисов: читатель находит книгу в библиотеке, берёт её в аренду
и возвращает. Количество звёзд рейтинга задаёт, сколько книг можно держать на руках
одновременно.

## Сервисы

| Сервис | Порт | База | Отвечает за |
|---|---|---|---|
| gateway-service | 8080 | — | единая точка входа, оркестрация вызовов |
| reservation-service | 8070 | reservations | брони: кто, что, где, до какой даты |
| library-service | 8060 | libraries | библиотеки, книги, счётчик доступных экземпляров |
| rating-service | 8050 | ratings | рейтинг читателя в звёздах |

Сервисы между собой не общаются — все вызовы идут через gateway.

## API

```
GET  /api/v1/libraries?city=&page=&size=
GET  /api/v1/libraries/{libraryUid}/books?showAll=&page=&size=
GET  /api/v1/reservations                            X-User-Name
POST /api/v1/reservations                            X-User-Name
POST /api/v1/reservations/{reservationUid}/return    X-User-Name
GET  /api/v1/rating                                  X-User-Name
```

Полное описание — в [v4/[inst][v4] Library System.yml](<v4/[inst][v4] Library System.yml>).

## Правила начисления звёзд

Новый читатель получает 75 звёзд. При возврате:

* просрочка — минус 10;
* состояние хуже, чем при выдаче, — минус 10;
* возврат в срок и без ухудшения — плюс 1.

Итоговое значение ограничено диапазоном 1–100.

## Запуск

```shell
docker compose up -d --build
```

Порт Postgres можно переопределить через `POSTGRES_PORT` в `.env` (см. `.env.example`),
если 5432 на машине уже занят.

Справочные данные варианта library-service заводит сам при старте, отдельного
init-скрипта для них нет.

## Тесты

Unit-тесты идут на настоящем Postgres и используют базы `*_test`, поэтому не задевают
данные, на которых работает коллекция Postman.

```shell
export PG=postgresql+psycopg://program:test@localhost:5432
(cd library-service     && TEST_DATABASE_URL=$PG/libraries_test    python -m pytest)
(cd reservation-service && TEST_DATABASE_URL=$PG/reservations_test python -m pytest)
(cd rating-service      && TEST_DATABASE_URL=$PG/ratings_test      python -m pytest)
(cd gateway-service     && python -m pytest)
```

Тестам gateway база не нужна — он ходит только по HTTP, и в тестах этот транспорт
подменяется заглушкой.

Интеграционные:

```shell
newman run -e v4/postman/environment.json v4/postman/collection.json
```

## Замечания

* Init-скрипты Postgres выполняются только на пустом томе — после правок в `postgres/`
  нужен `docker compose down -v`.
* Версию образа Postgres выше 13 поднимать нельзя: начиная с 15-й роль, не владеющая
  базой, теряет право создавать таблицы в схеме `public`.
