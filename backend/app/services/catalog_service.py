import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, or_, and_
from backend.app.models.catalog import Product, Category, Inventory, ProductVariant
from backend.app.schemas.catalog_schema import CanonicalProduct, CatalogSearchFilter, ProductResponse

class CatalogService:
    @staticmethod
    def slugify(text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        return re.sub(r'[\s_-]+', '-', text)

    @staticmethod
    def import_canonical_product(db: Session, item: CanonicalProduct, merchant_id: Optional[str] = None) -> Product:
        """Imports or updates a product into the canonical database schema."""
        cat_slug = item.category_slug or CatalogService.slugify(item.category_name or "General")
        cat_stmt = select(Category).where(Category.slug == cat_slug)
        category = db.execute(cat_stmt).scalar_one_or_none()

        if not category:
            category = Category(
                name=item.category_name or item.category_slug.replace("-", " ").title(),
                slug=cat_slug,
                merchant_id=merchant_id
            )
            db.add(category)
            db.flush()

        prod_stmt = select(Product).options(joinedload(Product.inventory), joinedload(Product.category)).where(Product.sku == item.sku)
        product = db.execute(prod_stmt).scalar_one_or_none()

        slug = item.slug or CatalogService.slugify(item.name)
        if not product:
            product = Product(
                merchant_id=merchant_id,
                category_id=category.id,
                sku=item.sku,
                name=item.name,
                slug=slug,
                description=item.description,
                brand=item.brand,
                base_price=item.base_price,
                compare_at_price=item.compare_at_price,
                currency=item.currency,
                tags=item.tags,
                attributes=item.attributes,
                image_url=item.image_url,
                rating=item.rating,
                review_count=item.review_count,
                is_active=item.is_active
            )
            db.add(product)
            db.flush()

            inv = Inventory(
                product_id=product.id,
                stock_quantity=item.stock_quantity,
                reserved_quantity=0,
                is_available=item.stock_quantity > 0
            )
            db.add(inv)
        else:
            product.name = item.name
            product.description = item.description
            product.base_price = item.base_price
            product.compare_at_price = item.compare_at_price
            product.tags = item.tags
            product.attributes = item.attributes
            product.image_url = item.image_url or product.image_url
            product.category_id = category.id
            if product.inventory:
                product.inventory.stock_quantity = item.stock_quantity
                product.inventory.is_available = item.stock_quantity > 0

        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def search_catalog(db: Session, search_filter: CatalogSearchFilter) -> List[ProductResponse]:
        """Searches products with keyword matching, price range, and category filters."""
        stmt = select(Product).options(joinedload(Product.inventory), joinedload(Product.category)).where(Product.is_active == True)

        if search_filter.category:
            cat_slug = search_filter.category.lower()
            stmt = stmt.join(Product.category).where(or_(Category.slug == cat_slug, Category.name.ilike(f"%{cat_slug}%")))

        if search_filter.min_price is not None:
            stmt = stmt.where(Product.base_price >= search_filter.min_price)

        if search_filter.max_price is not None:
            stmt = stmt.where(Product.base_price <= search_filter.max_price)

        if search_filter.query:
            q = f"%{search_filter.query}%".lower()
            stmt = stmt.where(
                or_(
                    Product.name.ilike(q),
                    Product.description.ilike(q),
                    Product.brand.ilike(q),
                    Product.sku.ilike(q)
                )
            )

        stmt = stmt.limit(search_filter.limit).offset(search_filter.offset)
        products = db.execute(stmt).scalars().unique().all()

        results = []
        for p in products:
            stock_qty = p.inventory.stock_quantity if p.inventory else 0
            is_avail = p.inventory.is_available if p.inventory else False
            
            if search_filter.in_stock_only and stock_qty <= 0:
                continue

            results.append(ProductResponse(
                id=p.id,
                sku=p.sku,
                name=p.name,
                slug=p.slug,
                category_name=p.category.name if p.category else None,
                category_slug=p.category.slug if p.category else None,
                description=p.description,
                brand=p.brand,
                base_price=p.base_price,
                compare_at_price=p.compare_at_price,
                currency=p.currency,
                stock_quantity=stock_qty,
                is_available=is_avail,
                tags=p.tags or [],
                attributes=p.attributes or {},
                image_url=p.image_url,
                rating=p.rating,
                review_count=p.review_count
            ))
        return results

    @staticmethod
    def get_product(db: Session, product_id_or_sku: str) -> Optional[ProductResponse]:
        stmt = (
            select(Product)
            .options(joinedload(Product.inventory), joinedload(Product.category))
            .where(or_(Product.id == product_id_or_sku, Product.sku == product_id_or_sku))
        )
        p = db.execute(stmt).scalars().unique().first()
        if not p:
            return None

        stock_qty = p.inventory.stock_quantity if p.inventory else 0
        is_avail = p.inventory.is_available if p.inventory else False

        return ProductResponse(
            id=p.id,
            sku=p.sku,
            name=p.name,
            slug=p.slug,
            category_name=p.category.name if p.category else None,
            category_slug=p.category.slug if p.category else None,
            description=p.description,
            brand=p.brand,
            base_price=p.base_price,
            compare_at_price=p.compare_at_price,
            currency=p.currency,
            stock_quantity=stock_qty,
            is_available=is_avail,
            tags=p.tags or [],
            attributes=p.attributes or {},
            image_url=p.image_url,
            rating=p.rating,
            review_count=p.review_count
        )
