from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated, List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form  # , Path
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, LargeBinary, select, delete  # , insert, update, all
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import bcrypt
from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response

# блок переменных

# блок создания объектов
# Создание объекта FastAPI
app = FastAPI()

# Настройка базы данных MySQL
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://isp_p_Shabanov:12345@77.91.86.135/bor"
SECRET_KEY = "804g087g07f350yf35fhbwreo67r89234fvwrefv9483fgv2t7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# блок создания объектов

# блок создания схем
# Определение модели SQLAlchemy для пользователя
class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(100))
    disabled = Column(Boolean, default=False)


class product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    price = Column(Integer)
    amount = Column(Integer)
    description = Column(String(500))
    seller_id = Column(Integer, ForeignKey('user.id'))
    image = Column(LargeBinary(length=16777215))  # Add this field for storing image data
    image_type = Column(String(20))  # Add this field for storing image MIME type


class product_user(Base):
    __tablename__ = "basket"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('product.id'))
    amount = Column(Integer)
    user_id = Column(Integer, ForeignKey('user.id'))


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    giga_order_id = Column(Integer, ForeignKey("giga_orders.id"))  # добавлено
    user_id = Column(Integer, ForeignKey("user.id"))
    product_name = Column(String(50))
    quantity = Column(Integer)
    price = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class GigaOrder(Base):
    __tablename__ = "giga_orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    total_price = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


# Создание таблиц в базе данных
Base.metadata.create_all(bind=engine)
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    disabled: bool | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    disabled: bool | None = None

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class ProductCreate(BaseModel):
    name: str
    price: int
    amount: int
    description: str


class ProductUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    disabled: bool | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    price: int
    amount: int
    description: str
    seller_id: int
    image_type: str

    class Config:
        from_attributes = True
        # json_encoders = {bytes: lambda v: None}  # Skip binary data during JSON serialization


class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_name: str
    quantity: int
    price: float
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItem(BaseModel):
    id: int
    product_name: str
    quantity: int
    price: int
    created_at: datetime

    class Config:
        from_attributes = True


class GigaOrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: int
    created_at: datetime
    items: List[OrderItem]

    class Config:
        from_attributes = True


# блок создания схем

# блок функций
# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)  # Используем правильную функцию
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_basket_price(db: Session, user_id: int, result=0):
    select_query = select(product.price).join(product_user).filter(product_user.user_id == user_id).all()
    for i in select_query:
        result += i
    return result


def basket_delete(db: Session, product_id: int, user_id: int):
    delete(product_user).filter([product_user.product_id == product_id, product_user.user_id == user_id]).all()


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user_by_username(username=token_data.username, db=db)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# блок функций

# блок маршрутов
@app.get("/", response_class=HTMLResponse)
async def get_client():
    with open("static/home-page.html", "r", encoding="utf-8") as file:
        return file.read()


@app.post("/register/", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = hash_password(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or Email already registered")


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    if not users:
        raise HTTPException(status_code=404, detail="Users not found")
    return users


# Маршрут для создания нового пользователя


@app.get("/items/")
async def read_items(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token": token}


@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_active_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only update your profile")
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user_update.username:
        user.username = user_update.username
    if user_update.email:
        user.email = user_update.email
    if user_update.password:
        user.hashed_password = hash_password(user_update.password)
    if user_update.disabled is not None:
        user.disabled = user_update.disabled
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or Email already registered")


# Маршрут для удаления пользователя по ID
@app.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your profile")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return user


@app.post("/basket/add")
def add_to_basket(product_id: int, amount: int, current_user: User = Depends(get_current_active_user),
                  db: Session = Depends(get_db)):
    product_obj = db.query(product).filter(product.id == product_id).first()
    if not product_obj:
        raise HTTPException(status_code=404, detail="Product not found")
    basket_entry = product_user(product_id=product_id, amount=amount, user_id=current_user.id)
    db.add(basket_entry)
    db.commit()
    db.refresh(basket_entry)
    return {"message": "Product added to basket", "basket_id": basket_entry.id}


@app.delete("/basket/{product_id}")
def delete_from_basket(product_id: int, db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_active_user)):
    item = db.query(product_user).filter_by(product_id=product_id, user_id=current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in basket")
    db.delete(item)
    db.commit()
    return {"detail": "Item removed from basket"}


@app.get("/basket/")
def get_basket(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    items = db.query(product, product_user.amount).join(product_user).filter(
        product_user.user_id == current_user.id).all()
    return [{"id": p.id, "name": p.name, "price": p.price, "amount": a} for p, a in items]


@app.post("/orders/add")
def create_order(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    basket_items = db.query(product_user).filter_by(user_id=current_user.id).all()
    if not basket_items:
        raise HTTPException(status_code=400, detail="Basket is empty")

    total = 0
    orders_to_add = []
    for item in basket_items:
        prod = db.query(product).filter_by(id=item.product_id).first()
        if prod.amount < item.amount:
            raise HTTPException(status_code=400, detail=f"Not enough stock for {prod.name}")
        prod.amount -= item.amount
        order_price = prod.price * item.amount
        total += order_price
        orders_to_add.append((prod.name, item.amount, order_price))

    giga_order = GigaOrder(user_id=current_user.id, total_price=total)
    db.add(giga_order)
    db.commit()
    db.refresh(giga_order)

    for name, qty, price in orders_to_add:
        order = Order(
            giga_order_id=giga_order.id,
            user_id=current_user.id,
            product_name=name,
            quantity=qty,
            price=price
        )
        db.add(order)

    db.query(product_user).filter_by(user_id=current_user.id).delete()
    db.commit()

    return {"detail": "Giga order placed", "total_price": total, "giga_order_id": giga_order.id}


@app.post("/sales/add", response_model=ProductResponse)
async def post_sale(
        name: str = Form(...),
        price: int = Form(...),
        amount: int = Form(...),
        description: str = Form(...),
        image: UploadFile = File(None),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    image_data = None
    image_type = None

    if image:
        image_data = await image.read()
        image_type = image.content_type

    new_product = product(
        name=name,
        price=price,
        amount=amount,
        description=description,
        seller_id=current_user.id,
        image=image_data,
        image_type=image_type
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    # Convert to Pydantic model which will handle the binary data properly
    return ProductResponse.from_orm(new_product)


@app.delete("/sales/{product_id}")
def delete_sale(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    prod = db.query(product).filter_by(id=product_id, seller_id=current_user.id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found or not yours")
    db.delete(prod)
    db.commit()
    return {"detail": "Sale deleted"}


@app.get("/sales/", response_model=List[ProductResponse])
def get_sales(db: Session = Depends(get_db)):
    sales = db.query(product).all()
    return sales


@app.get("/sales/me", response_model=List[ProductResponse])
def get_my_sales(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    sales = db.query(product).filter_by(seller_id=current_user.id).all()
    if not sales:
        raise HTTPException(status_code=404, detail="You have not your own products")
    return sales


@app.get("/sales/search/{product_name}", response_model=List[ProductResponse])
def search_products(product_name: str, db: Session = Depends(get_db)):
    sales = db.query(product).filter(product.name.contains(product_name)).all()
    if not sales:
        raise HTTPException(status_code=404, detail="Products not found")
    return sales


@app.get("/products/{product_id}/image")
async def get_product_image(product_id: int, db: Session = Depends(get_db)):
    product_img = db.query(product).filter(product.id == product_id).first()
    if not product_img or not product_img.image:
        raise HTTPException(status_code=404, detail="Image not found")

    return Response(content=product_img.image, media_type=product_img.image_type)


@app.put("/sales/{product_id}")
def update_sale(product_id: int, name: str | None = None, price: int | None = None,
                amount: int | None = None, description: str | None = None,
                db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    prod = db.query(product).filter_by(id=product_id, seller_id=current_user.id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found or not yours")

    if name: prod.name = name
    if price is not None: prod.price = price
    if amount is not None: prod.amount = amount
    if description: prod.description = description

    db.commit()
    db.refresh(prod)
    return prod


@app.get("/giga_orders/{giga_order_id}", response_model=GigaOrderResponse)
def get_giga_order_by_id(giga_order_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_active_user)):
    giga_order = db.query(GigaOrder).filter_by(id=giga_order_id, user_id=current_user.id).first()
    if not giga_order:
        raise HTTPException(status_code=404, detail="Giga order not found")

    orders = db.query(Order).filter_by(giga_order_id=giga_order.id).all()

    return GigaOrderResponse(
        id=giga_order.id,
        user_id=giga_order.user_id,
        total_price=giga_order.total_price,
        created_at=giga_order.created_at,
        items=orders
    )


@app.get("/giga_orders", response_model=List[GigaOrderResponse])
def get_giga_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    giga_orders = db.query(GigaOrder).filter_by(user_id=current_user.id).all()
    result = []
    for go in giga_orders:
        orders = db.query(Order).filter_by(giga_order_id=go.id).all()
        result.append(
            GigaOrderResponse(
                id=go.id,
                user_id=go.user_id,
                total_price=go.total_price,
                created_at=go.created_at,
                items=orders
            )
        )
    return result
# блок маршрутов