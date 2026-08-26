import json
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import aio_pika
import uuid
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

RABBIT_URL = os.getenv("RABBITMQ_URL")

@app.on_event("startup")
async def startup():
    app.state.connection = await aio_pika.connect_robust(RABBIT_URL)
    app.state.channel = await app.state.connection.channel()
    app.state.callback_queue = await app.state.channel.declare_queue(exclusive=True)

    async def on_response(message: aio_pika.IncomingMessage):
        correlation_id = message.correlation_id
        future = app.state.futures.pop(correlation_id, None)
        if future:
            future.set_result(message.body.decode())

    await app.state.callback_queue.consume(on_response)
    app.state.futures = {}

async def rpc_call(queue_name: str, payload: dict):
    correlation_id = str(uuid.uuid4())
    future = asyncio.get_event_loop().create_future()
    app.state.futures[correlation_id] = future

    await app.state.channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(payload).encode(),
            reply_to=app.state.callback_queue.name,
            correlation_id=correlation_id
        ),
        routing_key=queue_name
    )
    result = await future
    return json.loads(result)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/auth/me")
async def get_me(token: str):
    return await rpc_call("auth_queue", {"action": "get_me", "token": token})

@app.get("/api/courses")
async def get_courses():
    return await rpc_call("course_queue", {"action": "get_courses"})

@app.post("/api/orders/add")
async def create_order(request: Request):
    data = await request.json()
    return await rpc_call("order_queue", {"action": "create_order", **data})

@app.get("/api/search/{name}")
async def search_products(name: str):
    return await rpc_call("search_queue", {"action": "search", "query": name})

@app.post("/api/notify/email")
async def notify_email(request: Request):
    data = await request.json()
    await app.state.channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps({"type": "email", **data}).encode()),
        routing_key="notification_queue"
    )
    return {"status": "sent"}
