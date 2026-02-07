from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AddProductToOrderRequest(BaseModel):
    """Request body for adding a product to an order."""

    product_id: int = Field(..., gt=0, description="ID товара (номенклатуры)")
    quantity: int = Field(..., gt=0, le=10000, description="Количество (должно быть > 0)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "quantity": 2,
            }
        }
    )


class ProductBrief(BaseModel):
    """Short product info embedded in response."""

    id: int
    name: str
    price: Decimal
    stock_quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    """Response returned after adding a product to an order."""

    id: int
    order_id: int
    product_id: int
    quantity: int
    price: Decimal
    product: Optional[ProductBrief] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail: str
