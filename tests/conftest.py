import asyncio
from decimal import Decimal
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.main import app
from app.models import Base, Customer, Item, Order, OrderItem

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seed_data(test_session: AsyncSession) -> dict:
    """Seed test data and return references."""
    # Create customer
    customer = Customer(id=1, name="Test Customer", email="test@example.com")
    test_session.add(customer)
    
    # Create items
    item1 = Item(
        id=1,
        sku="TEST-001",
        name="Test Item 1",
        price=Decimal("99.99"),
        stock_quantity=50,
    )
    item2 = Item(
        id=2,
        sku="TEST-002",
        name="Test Item 2",
        price=Decimal("149.99"),
        stock_quantity=10,
    )
    item3 = Item(
        id=3,
        sku="TEST-003",
        name="Out of Stock Item",
        price=Decimal("29.99"),
        stock_quantity=0,
    )
    test_session.add_all([item1, item2, item3])
    
    # Create orders
    order1 = Order(id=1, customer_id=1, status="new")
    order2 = Order(id=2, customer_id=1, status="new")
    test_session.add_all([order1, order2])
    
    # Add existing item to order2 for increment test
    existing_order_item = OrderItem(
        order_id=2,
        item_id=1,
        quantity=2,
        price=Decimal("99.99"),
    )
    test_session.add(existing_order_item)
    
    await test_session.commit()
    
    return {
        "customer": customer,
        "items": [item1, item2, item3],
        "orders": [order1, order2],
    }
