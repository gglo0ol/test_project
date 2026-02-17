from typing import Annotated

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import (
    AddProductToOrderRequest,
    ErrorResponse,
    OrderItemResponse,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_order_service(db: DbSession) -> OrderService:
    return OrderService(db)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


@router.post(
    "/{order_id}/items",
    response_model=OrderItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить товар в заказ",
    description=(
        "Добавляет товар (номенклатуру) в существующий заказ.\n\n"
        "- Если товар уже есть в заказе — увеличивает количество.\n"
        "- Если товара нет на складе — возвращает ошибку 400.\n"
        "- Цена фиксируется на момент добавления."
    ),
    responses={
        201: {"description": "Товар успешно добавлен"},
        400: {"model": ErrorResponse, "description": "Недостаточно товара на складе"},
        404: {"model": ErrorResponse, "description": "Заказ или товар не найден"},
    },
)
async def add_product_to_order(
    order_id: Annotated[int, Path(gt=0, description="ID заказа")],
    body: AddProductToOrderRequest,
    service: OrderServiceDep,
) -> OrderItemResponse:
    order_item = await service.add_product_to_order(
        order_id=order_id,
        product_id=body.product_id,
        quantity=body.quantity,
    )
    return OrderItemResponse.model_validate(order_item)
