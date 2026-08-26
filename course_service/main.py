import asyncio
import aio_pika
import json
import os
import time
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "sqlite:///./courses.db"
RABBIT_URL = os.getenv("RABBITMQ_URL")
print(f"[course_service] RABBIT_URL = {RABBIT_URL}")

Base = declarative_base()
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100))
    description = Column(String(500))
    price = Column(Integer)

Base.metadata.create_all(bind=engine)

async def handle_request(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            action = payload.get("action")
            if action == "get_courses":
                db = SessionLocal()
                courses = db.query(Course).all()
                db.close()
                result = [
                    {
                        "id": c.id,
                        "title": c.title,
                        "description": c.description,
                        "price": c.price
                    } for c in courses
                ]
                if message.reply_to:
                    await message.channel.default_exchange.publish(
                        aio_pika.Message(
                            body=json.dumps(result).encode(),
                            correlation_id=message.correlation_id
                        ),
                        routing_key=message.reply_to
                    )
        except Exception as e:
            print(f"[course_service] Failed to process message: {e}")

async def main():
    for attempt in range(10):
        try:
            print(f"[course_service] Trying to connect to RabbitMQ (attempt {attempt + 1}/10)...")
            connection = await aio_pika.connect_robust(RABBIT_URL)
            print("[course_service] Connected to RabbitMQ.")
            break
        except Exception as e:
            print(f"[course_service] RabbitMQ not ready: {e}")
            time.sleep(3)
    else:
        print("[course_service] Failed to connect to RabbitMQ after 10 attempts. Exiting.")
        return

    channel = await connection.channel()
    queue = await channel.declare_queue("course_queue", durable=True)
    print("[course_service] Listening on course_queue...")
    await queue.consume(handle_request)
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
