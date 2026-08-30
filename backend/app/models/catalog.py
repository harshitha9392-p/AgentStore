from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base
from backend.app.models.base import TimestampMixin

class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(String(36), ForeignKey("categories.id"), nullable=True)
    is_restricted = Column(Boolean, default=False)  # Category restriction gate flag

    products = relationship("Product", back_populates="category")

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    category_id = Column(String(36), ForeignKey("categories.id"), nullable=True, index=True)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    brand = Column(String(100), nullable=True, index=True)
    
    # Pricing & Currency
    base_price = Column(Float, nullable=False)
    compare_at_price = Column(Float, nullable=True)
    currency = Column(String(10), default="INR", nullable=False)
    
    # Metadata for AI Semantic Search and Reasoning
    tags = Column(JSON, default=list)
    attributes = Column(JSON, default=dict) # e.g. {"color": "Midnight Blue", "storage": "256GB"}
    image_url = Column(String(512), nullable=True)
    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

    category = relationship("Category", back_populates="products")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

class ProductVariant(Base, TimestampMixin):
    __tablename__ = "product_variants"

    product_id = Column(String(36), ForeignKey("products.id"), nullable=False, index=True)
    sku = Column(String(64), unique=True, index=True, nullable=False)
    title = Column(String(120), nullable=False)
    price_delta = Column(Float, default=0.0)
    attributes = Column(JSON, default=dict)
    stock_quantity = Column(Integer, default=10)

    product = relationship("Product", back_populates="variants")

class Inventory(Base, TimestampMixin):
    __tablename__ = "inventory"

    product_id = Column(String(36), ForeignKey("products.id"), unique=True, nullable=False, index=True)
    stock_quantity = Column(Integer, default=0, nullable=False)
    reserved_quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=5, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    product = relationship("Product", back_populates="inventory")
