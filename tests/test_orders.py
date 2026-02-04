"""
Tests for the Add Item to Order endpoint.

Test cases:
1. Happy path - add new item to order
2. Item not found - 404
3. Order not found - 404
4. Not enough stock - 400
5. Increment existing item quantity
6. Validation errors (negative quantity, etc.)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_add_item_to_order_success(client: AsyncClient, seed_data: dict) -> None:
    """Test successfully adding a new item to an order."""
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"item_id": 1, "quantity": 3},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["order_id"] == 1
    assert data["item_id"] == 1
    assert data["quantity"] == 3
    assert data["price"] == "99.99"
    assert data["item"] is not None
    assert data["item"]["name"] == "Test Item 1"


@pytest.mark.asyncio
async def test_add_item_order_not_found(client: AsyncClient, seed_data: dict) -> None:
    """Test adding item to non-existent order returns 404."""
    response = await client.post(
        "/api/v1/orders/9999/items",
        json={"item_id": 1, "quantity": 1},
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_item_item_not_found(client: AsyncClient, seed_data: dict) -> None:
    """Test adding non-existent item to order returns 404."""
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"item_id": 9999, "quantity": 1},
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_item_not_enough_stock(client: AsyncClient, seed_data: dict) -> None:
    """Test adding item with insufficient stock returns 400."""
    # Item 3 has 0 stock
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"item_id": 3, "quantity": 1},
    )
    
    assert response.status_code == 400
    assert "not enough stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_item_not_enough_stock_large_quantity(
    client: AsyncClient, seed_data: dict
) -> None:
    """Test adding more items than available in stock returns 400."""
    # Item 2 has 10 in stock, request 100
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"item_id": 2, "quantity": 100},
    )
    
    assert response.status_code == 400
    assert "not enough stock" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_item_increment_existing(client: AsyncClient, seed_data: dict) -> None:
    """Test that adding an existing item increments quantity instead of creating duplicate."""
    # Order 2 already has item 1 with quantity 2
    response = await client.post(
        "/api/v1/orders/2/items",
        json={"item_id": 1, "quantity": 3},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["order_id"] == 2
    assert data["item_id"] == 1
    # Should be 2 (existing) + 3 (new) = 5
    assert data["quantity"] == 5


@pytest.mark.asyncio
async def test_add_item_validation_negative_quantity(
    client: AsyncClient, seed_data: dict
) -> None:
    """Test that negative quantity returns validation error."""
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"item_id": 1, "quantity": -5},
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_item_validation_zero_quantity(
    client: AsyncClient, seed_data: dict
) -> None:
    """Test that zero quantity returns validation error."""
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"item_id": 1, "quantity": 0},
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_item_validation_missing_fields(
    client: AsyncClient, seed_data: dict
) -> None:
    """Test that missing required fields returns validation error."""
    response = await client.post(
        "/api/v1/orders/1/items",
        json={"quantity": 1},  # Missing item_id
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_add_item_validation_invalid_order_id(
    client: AsyncClient, seed_data: dict
) -> None:
    """Test that invalid order_id in path returns validation error."""
    response = await client.post(
        "/api/v1/orders/0/items",  # order_id must be > 0
        json={"item_id": 1, "quantity": 1},
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_order_success(client: AsyncClient, seed_data: dict) -> None:
    """Test successfully retrieving an order."""
    response = await client.get("/api/v1/orders/1")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == 1
    assert data["customer_id"] == 1
    assert data["status"] == "new"
    assert "order_items" in data


@pytest.mark.asyncio
async def test_get_order_not_found(client: AsyncClient, seed_data: dict) -> None:
    """Test retrieving non-existent order returns 404."""
    response = await client.get("/api/v1/orders/9999")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
