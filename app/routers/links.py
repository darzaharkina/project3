from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import random
import string
from typing import Optional, List

from app import models, schemas, auth
from app.database import get_db
from app.redis_client import cache_link, get_cached_link, delete_cached_link, cache_stats, get_cached_stats
from app.config import get_settings

router = APIRouter(prefix="/links", tags=["links"])
settings = get_settings()

def generate_short_code(length=6):
    """Генерация уникального короткого кода"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def get_unique_short_code(db: Session):
    """Получение уникального короткого кода"""
    while True:
        code = generate_short_code()
        if not db.query(models.Link).filter(models.Link.short_code == code).first():
            return code

# Обязательная функция 1: Создание короткой ссылки
@router.post("/shorten", response_model=schemas.LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_short_link(
    link_data: schemas.LinkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(auth.get_current_active_user)
):
    """Создание короткой ссылки (с поддержкой кастомного alias и времени жизни)"""
    
    # Проверка уникальности custom_alias
    if link_data.custom_alias:
        existing = db.query(models.Link).filter(
            (models.Link.short_code == link_data.custom_alias) |
            (models.Link.custom_alias == link_data.custom_alias)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom alias already exists"
            )
        short_code = link_data.custom_alias
    else:
        short_code = get_unique_short_code(db)
    
    # Создание ссылки
    db_link = models.Link(
        original_url=str(link_data.original_url),
        short_code=short_code,
        custom_alias=link_data.custom_alias,
        expires_at=link_data.expires_at,
        owner_id=current_user.id if current_user else None
    )
    
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    
    # Кэширование новой ссылки
    background_tasks.add_task(cache_link, short_code, str(link_data.original_url))
    
    return {
        "short_code": short_code,
        "original_url": str(link_data.original_url),
        "short_url": f"{settings.BASE_URL}/{short_code}",
        "created_at": db_link.created_at,
        "expires_at": db_link.expires_at,
        "is_active": db_link.is_active
    }

# Обязательная функция 1: Получение информации и редирект
@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Перенаправление на оригинальный URL"""
    
    # Проверка кэша
    cached_url = get_cached_link(short_code)
    if cached_url:
        # Обновляем статистику в фоне
        background_tasks.add_task(update_link_stats, short_code, db)
        return {"url": cached_url}
    
    # Поиск в БД
    link = db.query(models.Link).filter(
        (models.Link.short_code == short_code) | (models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if not link.is_active:
        raise HTTPException(status_code=410, detail="Link is deactivated")
    
    if link.expires_at and link.expires_at < datetime.utcnow():
        link.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="Link has expired")
    
    # Обновление статистики
    link.clicks += 1
    link.last_accessed = datetime.utcnow()
    db.commit()
    
    # Кэширование для будущих запросов
    background_tasks.add_task(cache_link, short_code, link.original_url)
    
    return {"url": link.original_url}

async def update_link_stats(short_code: str, db: Session):
    """Фоновая задача для обновления статистики"""
    link = db.query(models.Link).filter(
        (models.Link.short_code == short_code) | (models.Link.custom_alias == short_code)
    ).first()
    if link:
        link.clicks += 1
        link.last_accessed = datetime.utcnow()
        db.commit()

# Обязательная функция 1: Удаление ссылки
@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Удаление ссылки (только для авторизованных пользователей)"""
    
    link = db.query(models.Link).filter(
        (models.Link.short_code == short_code) | (models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    # Проверка прав (только владелец может удалить)
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(link)
    db.commit()
    
    # Удаление из кэша
    delete_cached_link(short_code)

# Обязательная функция 1: Обновление ссылки
@router.put("/{short_code}", response_model=schemas.LinkResponse)
async def update_link(
    short_code: str,
    link_update: schemas.LinkUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Обновление оригинального URL для короткой ссылки"""
    
    link = db.query(models.Link).filter(
        (models.Link.short_code == short_code) | (models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    if link.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    link.original_url = str(link_update.original_url)
    link.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(link)
    
    # Обновление кэша
    delete_cached_link(short_code)
    cache_link(short_code, link.original_url)
    
    return {
        "short_code": link.short_code,
        "original_url": link.original_url,
        "short_url": f"{settings.BASE_URL}/{link.short_code}",
        "created_at": link.created_at,
        "expires_at": link.expires_at,
        "is_active": link.is_active
    }

# Обязательная функция 2: Статистика по ссылке
@router.get("/{short_code}/stats", response_model=schemas.LinkStats)
async def get_link_stats(
    short_code: str,
    db: Session = Depends(get_db)
):
    """Получение статистики по ссылке"""
    
    # Проверка кэша
    cached_stats = get_cached_stats(short_code)
    if cached_stats:
        return cached_stats
    
    link = db.query(models.Link).filter(
        (models.Link.short_code == short_code) | (models.Link.custom_alias == short_code)
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    stats = {
        "original_url": link.original_url,
        "short_code": link.short_code,
        "clicks": link.clicks,
        "created_at": link.created_at,
        "last_accessed": link.last_accessed,
        "expires_at": link.expires_at,
        "owner_username": link.owner.username if link.owner else None
    }
    
    # Кэширование статистики
    cache_stats(short_code, stats)
    
    return stats

# Обязательная функция 4: Поиск по оригинальному URL
@router.get("/search", response_model=List[schemas.LinkSearchResponse])
async def search_by_original_url(
    original_url: str,
    db: Session = Depends(get_db)
):
    """
    Поиск ссылок по оригинальному URL
    """
    # Убираем сложности - просто получаем все ссылки
    all_links = db.query(models.Link).all()
    
    # Вручную фильтруем по вхождению подстроки (без учета регистра)
    search_lower = original_url.lower()
    matched_links = []
    
    for link in all_links:
        if search_lower in link.original_url.lower():
            matched_links.append({
                "short_code": link.short_code,
                "original_url": link.original_url,
                "created_at": link.created_at,
                "clicks": link.clicks
            })
    
    # Возвращаем максимум 20 результатов
    return matched_links[:20]

# Дополнительная функция: Удаление неиспользуемых ссылок
@router.delete("/cleanup/unused", status_code=status.HTTP_200_OK)
async def cleanup_unused_links(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Удаление неиспользуемых ссылок (только для админа/владельца)"""
    # В реальном проекте здесь должна быть проверка на админа
    
    cutoff_date = datetime.utcnow() - timedelta(days=settings.DEFAULT_EXPIRY_DAYS)
    
    unused_links = db.query(models.Link).filter(
        and_(
            models.Link.last_accessed < cutoff_date,
            models.Link.is_active == True
        )
    ).all()
    
    for link in unused_links:
        link.is_active = False
        delete_cached_link(link.short_code)
    
    db.commit()
    
    return {"message": f"Deactivated {len(unused_links)} unused links"}

# Дополнительная функция: История истекших ссылок
@router.get("/expired/history", response_model=List[schemas.LinkStats])
async def get_expired_links_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user)
):
    """Получение истории истекших ссылок"""
    
    expired_links = db.query(models.Link).filter(
        models.Link.expires_at < datetime.utcnow()
    ).all()
    
    return expired_links
