# Microservices Backend — Online Store

Микросервисная архитектура интернет-магазина на FastAPI + RabbitMQ.

Fork для команды разработчиков со стороны Backend-части. 
Проделана работа над:
- Backend-частью: создание и распределение микросервисов, добавление зависимостей с версиями;
- DevOps-частью: создание Docker-контейнера и развёртывание, отладка взаимодействия через через gateway;
- Проектировочной частью: анализ требований и распределение функционала на отдельные микросервисы, выделение необходимых ограничений и структуры всего проекта.

Дополнительно были взяты задачи по организации команды, распределению времени, согласованию проекта, информированию о текущей стадии разработки и проблемах.

---

## Сервисы

| Сервис             | Назначение                       |
|--------------------|----------------------------------|
| `auth_service`     | Авторизация и токены             |
| `user_service`     | CRUD по пользователю             |
| `product_service`  | Работа с товарами                |
| `order_service`    | Оформление заказов (GigaOrder)   |
| `basket_service`   | Корзина                          |
| `search_service`   | Поиск по товарам                 |
| `admin_service`    | Панель управления                |
| `notification_service` | Email-уведомления (RabbitMQ) |
| `course_service`   | RPC-сервис с курсами (пример)    |
| `gateway`          | Точка входа для всех запросов    |

---

## Запуск проекта

> Убедитесь, что установлен Docker и Docker Compose.

```bash
docker-compose up --build
```

После запуска:

- Gateway: [http://localhost:8000](http://localhost:8000)
- Swagger UI (документация): [http://localhost:8000/docs](http://localhost:8000/docs)
- RabbitMQ Management: [http://localhost:15672](http://localhost:15672)  
  Логин: `user3`, пароль: `password3`  
  Виртуальный хост: `/vhost_user3`

---

## Тесты и вызовы

Примеры RPC-запросов через `gateway`:

```bash
# Получение данных текущего пользователя (если токен действителен)
curl "http://localhost:8000/api/auth/me?token=..."

# Получение списка курсов через RPC
curl "http://localhost:8000/api/courses"

# Добавление заказа
curl -X POST http://localhost:8000/api/orders/add   -H "Content-Type: application/json"   -d '{
    "user_id": 1,
    "items": [{"product_name": "Book", "quantity": 2, "price": 500}]
  }'
```

---

## Разработка

- Python 3.10+
- FastAPI
- RabbitMQ (`aio_pika`)
- SQLite (локально)

---

## Структура проекта

```text
.
├── gateway/
│   ├── main.py
│   ├── requirements.txt
│   └── templates/index.html
├── auth_service/
├── user_service/
├── product_service/
├── order_service/
├── basket_service/
├── admin_service/
├── search_service/
├── notification_service/
├── course_service/
├── docker-compose.yml
├── .env
└── README.md
```