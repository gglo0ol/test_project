from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Item, Order, OrderItem


class OrderService:
    """Service layer for order-related business logic."""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def get_order_by_id(self, order_id: int) -> Order | None:
        """
        Fetch an order by ID with its items eagerly loaded.
        
        Args:
            order_id: The ID of the order to fetch.
            
        Returns:
            Order object if found, None otherwise.
        """
        query = (
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.item))
            .where(Order.id == order_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_item_by_id(self, item_id: int) -> Item | None:
        """
        Fetch an item by ID.
        
        Args:
            item_id: The ID of the item to fetch.
            
        Returns:
            Item object if found, None otherwise.
        """
        query = select(Item).where(Item.id == item_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_order_item(self, order_id: int, item_id: int) -> OrderItem | None:
        """
        Check if an item already exists in an order.
        
        Args:
            order_id: The order ID to check.
            item_id: The item ID to check.
            
        Returns:
            OrderItem if exists, None otherwise.
        """
        query = (
            select(OrderItem)
            .where(OrderItem.order_id == order_id, OrderItem.item_id == item_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def add_item_to_order(
        self,
        order_id: int,
        item_id: int,
        quantity: int,
    ) -> OrderItem:
        """
        Add an item to an order or increment quantity if already exists.
        
        Business logic:
        1. Check that order exists → 404 if not
        2. Check that item exists → 404 if not
        3. Check stock availability → 400 if insufficient
        4. If item already in order → update quantity
        5. If item not in order → create new order_item
        
        Args:
            order_id: The order to add the item to.
            item_id: The item to add.
            quantity: The quantity to add.
            
        Returns:
            The created or updated OrderItem.
            
        Raises:
            HTTPException: 404 if order/item not found, 400 if insufficient stock.
        """
        # 1. Check order exists
        order = await self.get_order_by_id(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order with id {order_id} not found"
            )
        
        # 2. Check item exists
        item = await self.get_item_by_id(item_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Item with id {item_id} not found"
            )
        
        # 3. Check stock availability
        if item.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock. Available: {item.stock_quantity}, requested: {quantity}"
            )
        
        # 4. Check if item already in order
        existing_order_item = await self.get_order_item(order_id, item_id)
        
        if existing_order_item:
            # Update existing order item - increment quantity
            new_total_quantity = existing_order_item.quantity + quantity
            
            # Re-check stock for total quantity
            if item.stock_quantity < quantity:  # We only check the additional quantity
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock. Available: {item.stock_quantity}, requested additional: {quantity}"
                )
            
            existing_order_item.quantity = new_total_quantity
            order_item = existing_order_item
        else:
            # 5. Create new order item
            order_item = OrderItem(
                order_id=order_id,
                item_id=item_id,
                quantity=quantity,
                price=item.price,  # Snapshot price at order time
            )
            self.db.add(order_item)
        
        # Flush to get the ID and ensure consistency
        await self.db.flush()
        
        # Refresh to load relationships
        await self.db.refresh(order_item, ["item"])
        
        return order_item
    
    async def recalculate_order_total(self, order_id: int) -> Decimal:
        """
        Recalculate and update the total amount for an order.
        
        Args:
            order_id: The order ID to recalculate.
            
        Returns:
            The new total amount.
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            return Decimal("0")
        
        total = sum(
            item.price * item.quantity
            for item in order.order_items
        )
        
        order.total_amount = total
        await self.db.flush()
        
        return total
