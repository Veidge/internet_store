from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session

DATABASE_URL = "sqlite:///./product.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# SQLAlchemy модель продукта
class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    price = Column(Integer)
    amount = Column(Integer)
    description = Column(String(500))
    seller_id = Column(Integer)
    image_type = Column(String(20))

# Pydantic модель
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

# Поиск продуктов по имени
@app.get("/sales/search/{product_name}", response_model=List[ProductResponse])
def search_products(product_name: str, db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.name.contains(product_name)).all()
    if not products:
        raise HTTPException(status_code=404, detail="Products not found")
    return products
