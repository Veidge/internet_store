from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from datetime import datetime
from pydantic import BaseModel
from typing import List

DATABASE_URL = "sqlite:///./admin.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# SQLAlchemy models
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    disabled = Column(Boolean, default=False)

class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50))
    price = Column(Integer)
    amount = Column(Integer)
    description = Column(String(500))
    seller_id = Column(Integer)
    image_type = Column(String(20))

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

# Pydantic models
class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    disabled: bool

    class Config:
        orm_mode = True

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

class ProductResponse(BaseModel):
    id: int
    name: str
    price: int
    amount: int
    description: str
    seller_id: int
    image_type: str

    class Config:
        orm_mode = True

# Dependency

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.get("/admin/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.delete("/admin/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user

@app.put("/admin/users/{user_id}/block", response_model=UserResponse)
def block_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.disabled = True
    db.commit()
    db.refresh(user)
    return user

@app.get("/admin/products", response_model=List[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.delete("/admin/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter_by(id=product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}

@app.get("/admin/giga_orders", response_model=List[GigaOrderResponse])
def get_all_giga_orders(db: Session = Depends(get_db)):
    giga_orders = db.query(GigaOrder).all()
    result = []
    for go in giga_orders:
        result.append(
            GigaOrderResponse(
                id=go.id,
                user_id=go.user_id,
                total_price=go.total_price,
                created_at=go.created_at,
                items=go.orders
            )
        )
    return result