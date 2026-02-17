from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import FastAPI

from app.api.router import api_router
from app.database import async_session_maker, engine
from app.models import Base, Order, Product


async def _seed_demo_data() -> None:
    """Insert demo data if the products table is empty."""
    from sqlalchemy import select, text

    async with async_session_maker() as session:
        result = await session.execute(select(Product).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # data already exists

        products = [
            Product(id=1, name="Смартфон X", price=Decimal("999.99"), stock_quantity=50),
            Product(id=2, name="Ноутбук Pro", price=Decimal("1499.99"), stock_quantity=20),
            Product(id=3, name="Книга Python", price=Decimal("49.99"), stock_quantity=100),
            Product(id=4, name="Книга SQL", price=Decimal("39.99"), stock_quantity=0),
        ]
        orders = [
            Order(id=1),
            Order(id=2),
        ]
        session.add_all(products + orders)
        await session.commit()

        # Reset sequences so next inserts don't collide with demo IDs
        await session.execute(text("SELECT setval('products_id_seq', 10, true)"))
        await session.execute(text("SELECT setval('orders_id_seq', 10, true)"))
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables and seed demo data on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_demo_data()
    yield


app = FastAPI(
    title="Order Service API",
    description="REST API для добавления товара в заказ",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    return {
        "service": "Order Service API",
        "version": "1.0.0",
        "docs": "/docs",
    }
