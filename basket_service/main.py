from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session

DATABASE_URL = "sqlite:///./basket.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# SQLAlchemy models
class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(Integer)
    price = Column(Integer)

class BasketItem(Base):
    __tablename__ = "basket"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("product.id"))
    user_id = Column(Integer, index=True)
    amount = Column(Integer)
    
    product = relationship("Product")

Base.metadata.create_all(bind=engine)

# Pydantic models
class BasketItemCreate(BaseModel):
    product_id: int
    amount: int
    user_id: int

class BasketItemResponse(BaseModel):
    id: int
    name: str
    price: int
    amount: int

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
@app.post("/basket/add")
def add_to_basket(item: BasketItemCreate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    basket_entry = BasketItem(product_id=item.product_id, amount=item.amount, user_id=item.user_id)
    db.add(basket_entry)
    db.commit()
    db.refresh(basket_entry)
    return {"message": "Product added to basket", "basket_id": basket_entry.id}

@app.delete("/basket/{product_id}")
def delete_from_basket(product_id: int, user_id: int, db: Session = Depends(get_db)):
    item = db.query(BasketItem).filter_by(product_id=product_id, user_id=user_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in basket")
    db.delete(item)
    db.commit()
    return {"detail": "Item removed from basket"}

@app.get("/basket/", response_model=List[BasketItemResponse])
def get_basket(user_id: int, db: Session = Depends(get_db)):
    items = db.query(BasketItem).join(Product).filter(BasketItem.user_id == user_id).all()
    return [
        BasketItemResponse(
            id=item.product.id,
            name=item.product.name,
            price=item.product.price,
            amount=item.amount
        ) for item in items
    ]
