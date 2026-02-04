from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AddItemToOrderRequest(BaseModel):
    """Request schema for adding an item to an order."""
    
    item_id: int = Field(..., gt=0, description="ID of the item to add")
    quantity: int = Field(..., gt=0, le=10000, description="Quantity to add (must be positive)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "item_id": 1,
                "quantity": 2
            }
        }
    )


class ItemResponse(BaseModel):
    """Response schema for item details."""
    
    id: int
    sku: Optional[str] = None
    name: str
    price: Decimal
    stock_quantity: int
    
    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    """Response schema for an order item (line item)."""
    
    id: int
    order_id: int
    item_id: int
    quantity: int
    price: Decimal
    item: Optional[ItemResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Response schema for a full order with items."""
    
    id: int
    customer_id: int
    status: str
    order_date: datetime
    total_amount: Decimal
    order_items: list[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    detail: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Order not found"
            }
        }
    )
