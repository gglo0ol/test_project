from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import (
    AddItemToOrderRequest,
    ErrorResponse,
    OrderItemResponse,
    OrderResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])


# Type alias for dependency injection
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_order_service(db: DbSession) -> OrderService:
    """Dependency to get OrderService instance."""
    return OrderService(db)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post(
    "/{order_id}/items",
    response_model=OrderItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add item to order",
    description="""
    Add an item to an existing order.
    
    - If the item is already in the order, increments the quantity
    - If the item is new to the order, creates a new line item
    - Validates stock availability before adding
    - Captures item price at the time of adding (price snapshot)
    """,
    responses={
        201: {"description": "Item successfully added to order"},
        400: {"model": ErrorResponse, "description": "Not enough stock or invalid request"},
        404: {"model": ErrorResponse, "description": "Order or item not found"},
        422: {"description": "Validation error"},
    },
)
async def add_item_to_order(
    order_id: Annotated[int, Path(gt=0, description="The ID of the order")],
    request: AddItemToOrderRequest,
    service: OrderServiceDep,
) -> OrderItemResponse:
    """
    Add an item to an order.
    
    - **order_id**: The order to add the item to
    - **item_id**: The item/product to add
    - **quantity**: How many units to add (must be > 0)
    
    Returns the created or updated order item with current item details.
    """
    order_item = await service.add_item_to_order(
        order_id=order_id,
        item_id=request.item_id,
        quantity=request.quantity,
    )
    
    return OrderItemResponse.model_validate(order_item)


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get order details",
    description="Retrieve a full order with all its items.",
    responses={
        200: {"description": "Order found"},
        404: {"model": ErrorResponse, "description": "Order not found"},
    },
)
async def get_order(
    order_id: Annotated[int, Path(gt=0, description="The ID of the order")],
    service: OrderServiceDep,
) -> OrderResponse:
    """
    Get order by ID with all items.
    
    Returns the full order including all line items and their product details.
    """
    from fastapi import HTTPException
    
    order = await service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    return OrderResponse.model_validate(order)
