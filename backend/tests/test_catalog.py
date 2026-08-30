import pytest
from backend.app.schemas.catalog_schema import CanonicalProduct, CatalogSearchFilter
from backend.app.services.catalog_service import CatalogService

def test_search_products_by_keyword(db_session):
    sf = CatalogSearchFilter(query="MacBook")
    results = CatalogService.search_catalog(db_session, sf)
    assert len(results) >= 1
    assert "MacBook" in results[0].name

def test_search_products_price_filter(db_session):
    sf = CatalogSearchFilter(min_price=1000, max_price=5000)
    results = CatalogService.search_catalog(db_session, sf)
    assert len(results) >= 1
    for r in results:
        assert 1000 <= r.base_price <= 5000

def test_import_canonical_product(db_session):
    item = CanonicalProduct(
        sku="TEST-SKU-999",
        name="Test Autonomous Drone",
        category_slug="electronics",
        description="A high tech drone for tests",
        base_price=4999.00,
        stock_quantity=15,
        currency="INR"
    )
    product = CatalogService.import_canonical_product(db_session, item)
    assert product.sku == "TEST-SKU-999"
    assert product.base_price == 4999.00
    assert product.inventory.stock_quantity == 15
