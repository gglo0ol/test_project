from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, Product


class OrderService:
    """Business logic for working with orders."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def add_product_to_order(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
    ) -> OrderItem:
        """
        Add a product to an order (or increase quantity if it already exists).

        Raises:
            HTTPException 404 — order or product not found.
            HTTPException 400 — insufficient stock.
        """
        # 1. Check that the order exists
        order = await self.db.get(Order, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Заказ с id {order_id} не найден",
            )

        # 2. Check that the product exists
        product = await self.db.get(Product, product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с id {product_id} не найден",
            )

        # 3. Look for an existing line item
        stmt = select(OrderItem).where(
            OrderItem.order_id == order_id,
            OrderItem.product_id == product_id,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        # 4. Calculate the required additional stock
        additional_qty = quantity
        if existing:
            # We need only `quantity` more items from stock
            total_qty = existing.quantity + quantity
        else:
            total_qty = quantity

        # 5. Stock check
        if product.stock_quantity < additional_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Недостаточно товара на складе. "
                    f"Доступно: {product.stock_quantity}, запрошено: {additional_qty}"
                ),
            )

        # 6. Decrease stock
        product.stock_quantity -= additional_qty

        # 7. Create or update order item
        if existing:
            existing.quantity = total_qty
            order_item = existing
        else:
            order_item = OrderItem(
                order_id=order_id,
                product_id=product_id,
                quantity=quantity,
                price=product.price,
            )
            self.db.add(order_item)

        await self.db.flush()
        await self.db.refresh(order_item, ["product"])

        return order_item
