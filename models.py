from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from db import Base

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    total_orders = Column(Integer, default=0)
    total_returns = Column(Integer, default=0)
    returns = relationship("ReturnRequest", back_populates="customer")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    sku = Column(String, index=True)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    status = Column(String, default="delivered")
    customer = relationship("Customer")

class ReturnRequest(Base):
    __tablename__ = "returns"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    order_id = Column(String, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    sku = Column(String, index=True)
    reason = Column(Text)
    image_path = Column(String, nullable=True)
    similarity_score = Column(Float, default=0.0)
    brightness = Column(Float, default=0.0)
    blur = Column(Float, default=0.0)
    metadata_score = Column(Float, default=0.0)
    text_consistency = Column(Float, default=0.0)
    customer_history = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)
    decision = Column(String, default="manual_review") 
    notes = Column(Text, nullable=True)

    customer = relationship("Customer", back_populates="returns")
