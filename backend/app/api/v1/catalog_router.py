from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.schemas.catalog_schema import CanonicalProduct, CatalogSearchFilter, ProductResponse, CatalogImportRequest
from backend.app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["Catalog"])

@router.get("/products", response_model=List[ProductResponse])
def search_products(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Category slug"),
    min_price: Optional[float] = Query(None, description="Min price"),
    max_price: Optional[float] = Query(None, description="Max price"),
    in_stock_only: bool = Query(True, description="Filter in-stock only"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    sf = CatalogSearchFilter(
        query=query,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        limit=limit,
        offset=offset
    )
    return CatalogService.search_catalog(db, sf)

@router.get("/products/{product_id_or_sku}", response_model=ProductResponse)
def get_product_details(
    product_id_or_sku: str,
    db: Session = Depends(get_db)
):
    prod = CatalogService.get_product(db, product_id_or_sku)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    return prod

@router.post("/import")
def import_products(
    payload: CatalogImportRequest,
    db: Session = Depends(get_db)
):
    imported = []
    for item_data in payload.products:
        canonical_item = CanonicalProduct(**item_data)
        p = CatalogService.import_canonical_product(db, canonical_item, merchant_id=payload.merchant_id)
        imported.append({"id": p.id, "sku": p.sku, "name": p.name})

    return {
        "success": True,
        "imported_count": len(imported),
        "products": imported
    }
