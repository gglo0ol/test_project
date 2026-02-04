from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    print("Starting up Order Service...")
    yield
    # Shutdown
    print("Shutting down Order Service...")


app = FastAPI(
    title="Order Service API",
    description="""
    REST API для управления заказами.
    
    ## Возможности
    
    * **Orders** - Управление заказами и позициями заказов
    * Добавление товаров в заказ
    * Получение информации о заказе
    
    ## Бизнес-логика
    
    При добавлении товара в заказ:
    - Проверяется существование заказа
    - Проверяется существование товара
    - Проверяется наличие на складе
    - Если товар уже есть в заказе — количество увеличивается
    - Если товара нет — создаётся новая позиция
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint with API info."""
    return {
        "service": "Order Service API",
        "version": "1.0.0",
        "docs": "/docs",
    }
