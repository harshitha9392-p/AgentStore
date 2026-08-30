from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CanonicalProduct(BaseModel):
    id: Optional[str] = None
    sku: str
    name: str
    slug: Optional[str] = None
    category_slug: str
    category_name: Optional[str] = None
    description: str
    brand: Optional[str] = None
    base_price: float = Field(..., gt=0)
    compare_at_price: Optional[float] = None
    currency: str = "INR"
    stock_quantity: int = Field(default=10, ge=0)
    tags: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    image_url: Optional[str] = None
    rating: float = 4.5
    review_count: int = 0
    is_active: bool = True

class CatalogImportRequest(BaseModel):
    merchant_id: Optional[str] = None
    source_format: str = "canonical_json"
    products: List[Dict[str, Any]]

class CatalogSearchFilter(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock_only: bool = True
    limit: int = 10
    offset: int = 0

class ProductResponse(BaseModel):
    id: str
    sku: str
    name: str
    slug: str
    category_name: Optional[str] = None
    category_slug: Optional[str] = None
    description: str
    brand: Optional[str] = None
    base_price: float
    compare_at_price: Optional[float] = None
    currency: str
    stock_quantity: int
    is_available: bool
    tags: List[str]
    attributes: Dict[str, Any]
    image_url: Optional[str] = None
    rating: float
    review_count: int

    model_config = ConfigDict(from_attributes=True)
