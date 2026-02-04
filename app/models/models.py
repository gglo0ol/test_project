from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class Category(Base):
    """Category model with self-referential parent relationship."""
    
    __tablename__ = "categories"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship("Category", back_populates="parent")
    items: Mapped[list["Item"]] = relationship("Item", back_populates="category")
    
    __table_args__ = (
        CheckConstraint("id != parent_id", name="chk_no_self_parent"),
    )


class Item(Base):
    """Item/Product model."""
    
    __tablename__ = "items"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sku: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="items")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="item")
    
    __table_args__ = (
        CheckConstraint("price >= 0", name="chk_item_price_positive"),
        CheckConstraint("stock_quantity >= 0", name="chk_stock_positive"),
    )


class Customer(Base):
    """Customer model."""
    
    __tablename__ = "customers"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")


class Order(Base):
    """Order model."""
    
    __tablename__ = "orders"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False
    )
    order_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(40), default="new")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_total_positive"),
    )


class OrderItem(Base):
    """Order item (line item) model."""
    
    __tablename__ = "order_items"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    order_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    item: Mapped["Item"] = relationship("Item", back_populates="order_items")
    
    __table_args__ = (
        UniqueConstraint("order_id", "item_id", name="unique_item_per_order"),
        CheckConstraint("quantity > 0", name="chk_quantity_positive"),
        CheckConstraint("price >= 0", name="chk_order_item_price_positive"),
    )
