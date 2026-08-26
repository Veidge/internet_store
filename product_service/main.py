from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# --- Настройка БД ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./products.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- Модель SQLAlchemy ---
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True)
    price = Column(Float)
    is_active = Column(Boolean, default=True)

# --- Создание таблиц ---
Base.metadata.create_all(bind=engine)

# --- Pydantic-схемы ---
class ProductCreate(BaseModel):
    title: str
    description: Optional[str]
    category: Optional[str]
    price: float
    is_active: Optional[bool] = True

class ProductResponse(ProductCreate):
    id: int

    class Config:
        orm_mode = True

# --- FastAPI-приложение ---
app = FastAPI(title="Product Service")

# --- Зависимость для получения сессии ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CRUD-методы ---

@app.post("/products", response_model=ProductResponse)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products", response_model=List[ProductResponse])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(Product).all()

@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, product_update: ProductCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product_update.dict().items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)
    return product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}