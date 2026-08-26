from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from datetime import datetime

DATABASE_URL = "sqlite:///./orders.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# SQLAlchemy Models
class GigaOrder(Base):
    __tablename__ = "giga_orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    total_price = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    orders = relationship("Order", back_populates="giga_order")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    giga_order_id = Column(Integer, ForeignKey("giga_orders.id"))
    user_id = Column(Integer)
    product_name = Column(String(50))
    quantity = Column(Integer)
    price = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    giga_order = relationship("GigaOrder", back_populates="orders")

Base.metadata.create_all(bind=engine)

# Pydantic Models
class OrderItem(BaseModel):
    id: int
    product_name: str
    quantity: int
    price: int
    created_at: datetime

    class Config:
        orm_mode = True

class GigaOrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: int
    created_at: datetime
    items: List[OrderItem]

    class Config:
        orm_mode = True

class GigaOrderCreateItem(BaseModel):
    product_name: str
    quantity: int
    price: int

class GigaOrderCreate(BaseModel):
    user_id: int
    items: List[GigaOrderCreateItem]

# Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.post("/orders/add", response_model=GigaOrderResponse)
def create_order(order_data: GigaOrderCreate, db: Session = Depends(get_db)):
    total = sum(item.price * item.quantity for item in order_data.items)
    giga_order = GigaOrder(user_id=order_data.user_id, total_price=total)
    db.add(giga_order)
    db.commit()
    db.refresh(giga_order)

    for item in order_data.items:
        order = Order(
            giga_order_id=giga_order.id,
            user_id=order_data.user_id,
            product_name=item.product_name,
            quantity=item.quantity,
            price=item.price * item.quantity,
        )
        db.add(order)

    db.commit()
    db.refresh(giga_order)
    return GigaOrderResponse(
        id=giga_order.id,
        user_id=giga_order.user_id,
        total_price=giga_order.total_price,
        created_at=giga_order.created_at,
        items=giga_order.orders
    )

@app.get("/giga_orders", response_model=List[GigaOrderResponse])
def get_giga_orders(user_id: int, db: Session = Depends(get_db)):
    giga_orders = db.query(GigaOrder).filter_by(user_id=user_id).all()
    return [
        GigaOrderResponse(
            id=go.id,
            user_id=go.user_id,
            total_price=go.total_price,
            created_at=go.created_at,
            items=go.orders
        ) for go in giga_orders
    ]

@app.get("/giga_orders/{giga_order_id}", response_model=GigaOrderResponse)
def get_giga_order_by_id(giga_order_id: int, db: Session = Depends(get_db)):
    giga_order = db.query(GigaOrder).filter_by(id=giga_order_id).first()
    if not giga_order:
        raise HTTPException(status_code=404, detail="Giga order not found")
    return GigaOrderResponse(
        id=giga_order.id,
        user_id=giga_order.user_id,
        total_price=giga_order.total_price,
        created_at=giga_order.created_at,
        items=giga_order.orders
    )
