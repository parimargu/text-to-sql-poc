"""Database models for retail stores and orders."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Store(Base):
    """Store model."""
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=False)
    manager = Column(String(100), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="store")


class Customer(Base):
    """Customer model."""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    """Product model."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    description = Column(Text)
    in_stock = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    """Order model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    store = relationship("Store", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Order item model."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")
