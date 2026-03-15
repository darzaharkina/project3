from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import logging

from app import models, schemas, auth
from app.database import engine, get_db
from app.routers import links
from app.config import get_settings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("Таблицы созданы")
except Exception as e:
    logger.error(f"Ошибка создания таблиц: {e}")
logger.info("=" * 50)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="URL Shortener API",
    description="API сервис для сокращения ссылок",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(links.router)

@app.get("/")
async def root():
    return {
        "message": "URL Shortener API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.post("/register", response_model=schemas.UserResponse)
async def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    logger.info(f"Попытка регистрации: {user_data.username}")
    
    # Проверка существующего пользователя
    existing_user = db.query(models.User).filter(
        (models.User.username == user_data.username) | 
        (models.User.email == user_data.email)
    ).first()
    
    if existing_user:
        logger.warning(f"Пользователь уже существует: {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Создание нового пользователя
    hashed_password = auth.get_password_hash(user_data.password)
    db_user = models.User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"Пользователь зарегистрирован: {user_data.username}")
    return db_user

@app.post("/token", response_model=schemas.Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Вход в систему и получение токена"""
    logger.info(f"Попытка входа: {form_data.username}")
    
    # Аутентификация
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Неудачная попытка входа: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создание токена
    access_token = auth.create_access_token(data={"sub": user.username})
    
    logger.info(f"Успешный вход: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Информация о текущем пользователе"""
    return current_user

# Альтернативный эндпоинт для тестирования авторизации
@app.get("/test-auth")
async def test_auth(
    current_user: models.User = Depends(auth.get_current_user)
):
    """Тестовый эндпоинт для проверки авторизации"""
    return {"message": f"Hello {current_user.username}, you are authenticated!"}
