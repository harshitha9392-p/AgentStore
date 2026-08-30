from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models.merchant import Merchant
from backend.app.models.catalog import Category, Product, Inventory
from backend.app.models.offer import Offer, BundleRule
from backend.app.models.policy import PolicyRule
from backend.app.services.audit_service import AuditService

def seed_database(db: Session):
    Base.metadata.create_all(bind=engine)

    m_stmt = select(Merchant).where(Merchant.slug == "novatech")
    merchant = db.execute(m_stmt).scalar_one_or_none()

    if not merchant:
        merchant = Merchant(
            name="NovaTech Flagship Store",
            slug="novatech",
            email="merchant@novatech.com",
            currency="INR",
            max_order_value=50000.0,
            max_discount_percentage=25.0,
            hitl_threshold=10000.0,
            daily_transaction_limit=100000.0
        )
        db.add(merchant)
        db.flush()

    categories_data = [
        {"name": "Laptops & Computers", "slug": "laptops-computers", "is_restricted": False, "desc": "High performance ultrabooks, laptops and computing accessories."},
        {"name": "Audio & Wearables", "slug": "audio-wearables", "is_restricted": False, "desc": "Premium wireless headphones, earbuds and smartwatches."},
        {"name": "Accessories & Gear", "slug": "accessories", "is_restricted": False, "desc": "Chargers, mice, sleeves, backpacks and everyday gear."},
        {"name": "Apparel & Lifestyle", "slug": "apparel", "is_restricted": False, "desc": "Tech-enabled lifestyle apparel and activewear."},
        {"name": "Restricted & Regulated Items", "slug": "restricted", "is_restricted": True, "desc": "Restricted goods requiring special permits / KYC."}
    ]

    cat_map = {}
    for c in categories_data:
        c_stmt = select(Category).where(Category.slug == c["slug"])
        cat = db.execute(c_stmt).scalar_one_or_none()
        if not cat:
            cat = Category(
                name=c["name"],
                slug=c["slug"],
                description=c["desc"],
                is_restricted=c["is_restricted"],
                merchant_id=merchant.id
            )
            db.add(cat)
            db.flush()
        cat_map[c["slug"]] = cat

    products_data = [
        {
            "sku": "APPLE-MBA-M3",
            "name": "Apple MacBook Air 15\" (M3 Chip, 16GB RAM, 512GB SSD)",
            "slug": "apple-macbook-air-15-m3",
            "category_slug": "laptops-computers",
            "brand": "Apple",
            "base_price": 134900.00,
            "compare_at_price": 144900.00,
            "stock": 8,
            "tags": ["laptop", "apple", "macbook", "m3", "ultrabook", "premium"],
            "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800&auto=format&fit=crop&q=60",
            "attributes": {"processor": "Apple M3", "ram": "16GB", "storage": "512GB SSD", "color": "Midnight Black"},
            "description": "Supercharged by the next-generation M3 chip, the 15-inch MacBook Air delivers incredible performance and up to 18 hours of battery life."
        },
        {
            "sku": "DELL-XPS-13",
            "name": "Dell XPS 13 Plus (Intel Core i7 13th Gen, 16GB, 1TB SSD)",
            "slug": "dell-xps-13-plus",
            "category_slug": "laptops-computers",
            "brand": "Dell",
            "base_price": 89990.00,
            "compare_at_price": 99990.00,
            "stock": 12,
            "tags": ["laptop", "dell", "xps", "windows", "ultrabook"],
            "image_url": "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=800&auto=format&fit=crop&q=60",
            "attributes": {"processor": "Intel Core i7-1360P", "ram": "16GB", "storage": "1TB SSD", "display": "OLED 3.5K"},
            "description": "Crafted with CNC machined aluminum, the Dell XPS 13 Plus is the pinnacle of compact elegance and compute speed."
        },
        {
            "sku": "SONY-WH1000XM5",
            "name": "Sony WH-1000XM5 Noise Canceling Wireless Headphones",
            "slug": "sony-wh1000xm5-wireless-headphones",
            "category_slug": "audio-wearables",
            "brand": "Sony",
            "base_price": 29990.00,
            "compare_at_price": 34990.00,
            "stock": 25,
            "tags": ["headphones", "sony", "anc", "audio", "wireless", "bluetooth"],
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&auto=format&fit=crop&q=60",
            "attributes": {"battery_life": "30 Hours", "noise_cancellation": "Auto NC Optimizer", "driver": "30mm Carbon Fiber"},
            "description": "Industry-leading noise cancellation with 8 microphones and Auto NC Optimizer. High-Resolution Audio wireless support."
        },
        {
            "sku": "BOAT-ROCK-450",
            "name": "boAt Rockerz 450 Pro Wireless On-Ear Headphones",
            "slug": "boat-rockerz-450-pro",
            "category_slug": "audio-wearables",
            "brand": "boAt",
            "base_price": 1499.00,
            "compare_at_price": 3990.00,
            "stock": 50,
            "tags": ["headphones", "boat", "budget", "wireless", "bass"],
            "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=800&auto=format&fit=crop&q=60",
            "attributes": {"playback": "70 Hours", "drivers": "40mm", "fast_charge": "ASAP Charge 10min = 10hrs"},
            "description": "Massive 70-hour playback with booming 40mm dynamic drivers and lightweight ergonomic design."
        },
        {
            "sku": "INCASE-SLV-15",
            "name": "Incase Premium Leather Protective Laptop Sleeve 15\"",
            "slug": "incase-leather-laptop-sleeve-15",
            "category_slug": "accessories",
            "brand": "Incase",
            "base_price": 3499.00,
            "compare_at_price": 4499.00,
            "stock": 30,
            "tags": ["sleeve", "case", "laptop accessory", "leather", "protection"],
            "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=800&auto=format&fit=crop&q=60",
            "attributes": {"material": "Full-grain Eco Leather", "cushioning": "Tensaerlite shock protection"},
            "description": "Tailored fit with magnetic snap closure and plush faux-fur interior lining to safeguard your laptop."
        },
        {
            "sku": "LOGI-MX-3S",
            "name": "Logitech MX Master 3S Wireless Performance Mouse",
            "slug": "logitech-mx-master-3s",
            "category_slug": "accessories",
            "brand": "Logitech",
            "base_price": 8995.00,
            "compare_at_price": 10995.00,
            "stock": 20,
            "tags": ["mouse", "logitech", "mx master", "productivity", "wireless"],
            "image_url": "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800&auto=format&fit=crop&q=60",
            "attributes": {"sensor": "8000 DPI Darkfield", "clicks": "Quiet Clicks 90% noise reduction", "wheel": "MagSpeed Electromagnetic"},
            "description": "An icon remastered with 8K DPI track-on-glass sensor and whisper-quiet tactile switches."
        },
        {
            "sku": "ANKER-GAN-65W",
            "name": "Anker 735 65W GaNPrime Fast Wall Charger",
            "slug": "anker-735-65w-ganprime-charger",
            "category_slug": "accessories",
            "brand": "Anker",
            "base_price": 2499.00,
            "compare_at_price": 3999.00,
            "stock": 40,
            "tags": ["charger", "anker", "gan", "fast charging", "usb-c"],
            "image_url": "https://images.unsplash.com/photo-1583863788434-e58a36330cf0?w=800&auto=format&fit=crop&q=60",
            "attributes": {"ports": "2x USB-C, 1x USB-A", "output": "65W Max PowerIQ 4.0"},
            "description": "Charge 3 devices simultaneously with cutting-edge Gallium Nitride (GaN) efficiency in an ultra-compact body."
        },
        {
            "sku": "URBAN-PACK-30L",
            "name": "Urban Tech Commuter Waterproof Backpack 30L",
            "slug": "urban-tech-waterproof-backpack",
            "category_slug": "accessories",
            "brand": "UrbanGear",
            "base_price": 2999.00,
            "compare_at_price": 4999.00,
            "stock": 18,
            "tags": ["backpack", "travel", "waterproof", "bag"],
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=800&auto=format&fit=crop&q=60",
            "attributes": {"capacity": "30L", "waterproof": "IPX4 Coated", "compartments": "Dedicated 16\" padded laptop compartment"},
            "description": "Weatherproof everyday commuter backpack with ergonomic airflow back panel and hidden anti-theft pocket."
        },
        {
            "sku": "RESTRICTED-DRONE-X",
            "name": "AeroTech Heavy-Payload Tactical Drone Prototype X",
            "slug": "aerotech-heavy-payload-tactical-drone",
            "category_slug": "restricted",
            "brand": "AeroTech",
            "base_price": 45000.00,
            "compare_at_price": 55000.00,
            "stock": 2,
            "tags": ["drone", "restricted", "tactical"],
            "image_url": "https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=800&auto=format&fit=crop&q=60",
            "attributes": {"license_required": "DGCA Category B", "range": "20KM"},
            "description": "Restricted dual-use tactical hardware. Sale prohibited without verified government license."
        }
    ]

    prod_map = {}
    for p in products_data:
        p_stmt = select(Product).where(Product.sku == p["sku"])
        prod = db.execute(p_stmt).scalar_one_or_none()

        cat = cat_map[p["category_slug"]]
        if not prod:
            prod = Product(
                merchant_id=merchant.id,
                category_id=cat.id,
                sku=p["sku"],
                name=p["name"],
                slug=p["slug"],
                brand=p["brand"],
                base_price=p["base_price"],
                compare_at_price=p["compare_at_price"],
                currency="INR",
                tags=p["tags"],
                attributes=p["attributes"],
                image_url=p["image_url"],
                description=p["description"]
            )
            db.add(prod)
            db.flush()

            inv = Inventory(
                product_id=prod.id,
                stock_quantity=p["stock"],
                reserved_quantity=0,
                is_available=p["stock"] > 0
            )
            db.add(inv)
        prod_map[p["sku"]] = prod

    bundle_rules_data = [
        {
            "trigger_sku": "APPLE-MBA-M3",
            "recommended_sku": "INCASE-SLV-15",
            "discount_pct": 15.0,
            "pitch_text": "🛡️ Protect your new MacBook! Add the Incase Leather Sleeve with 15% instant bundle savings."
        },
        {
            "trigger_sku": "APPLE-MBA-M3",
            "recommended_sku": "LOGI-MX-3S",
            "discount_pct": 10.0,
            "pitch_text": "⚡ Boost your workflow: Pair with Logitech MX Master 3S for 10% bundle off."
        },
        {
            "trigger_sku": "DELL-XPS-13",
            "recommended_sku": "INCASE-SLV-15",
            "discount_pct": 15.0,
            "pitch_text": "🛡️ Keep your XPS pristine: Bundle the Incase Leather Sleeve with 15% discount."
        },
        {
            "trigger_sku": "SONY-WH1000XM5",
            "recommended_sku": "ANKER-GAN-65W",
            "discount_pct": 20.0,
            "pitch_text": "🔋 Never run out of juice: Bundle the Anker 65W GaN Fast Charger for 20% off!"
        }
    ]

    for b in bundle_rules_data:
        trig = prod_map.get(b["trigger_sku"])
        rec = prod_map.get(b["recommended_sku"])
        if trig and rec:
            b_stmt = select(BundleRule).where(
                BundleRule.trigger_product_id == trig.id,
                BundleRule.recommended_product_id == rec.id
            )
            if not db.execute(b_stmt).scalar_one_or_none():
                rule = BundleRule(
                    trigger_product_id=trig.id,
                    recommended_product_id=rec.id,
                    bundle_discount_pct=b["discount_pct"],
                    pitch_text=b["pitch_text"],
                    is_active=True
                )
                db.add(rule)

    offers_data = [
        {
            "code": "SAVE10",
            "title": "10% Instant Cart Discount",
            "description": "Get 10% off on all cart orders above ₹2,000 (up to ₹1,000 off).",
            "discount_type": "PERCENTAGE",
            "discount_value": 10.0,
            "min_cart_value": 2000.0,
            "max_discount_cap": 1000.0
        },
        {
            "code": "FESTIVE20",
            "title": "20% Festive Super Saver",
            "description": "Unlock 20% discount on cart orders above ₹5,000 (up to ₹2,000 off).",
            "discount_type": "PERCENTAGE",
            "discount_value": 20.0,
            "min_cart_value": 5000.0,
            "max_discount_cap": 2000.0
        },
        {
            "code": "WELCOME100",
            "title": "₹100 Welcome Gift",
            "description": "Flat ₹100 instant discount on any purchase above ₹500.",
            "discount_type": "FIXED",
            "discount_value": 100.0,
            "min_cart_value": 500.0,
            "max_discount_cap": 100.0
        }
    ]

    for o in offers_data:
        o_stmt = select(Offer).where(Offer.code == o["code"])
        if not db.execute(o_stmt).scalar_one_or_none():
            db.add(Offer(
                code=o["code"],
                title=o["title"],
                description=o["description"],
                discount_type=o["discount_type"],
                discount_value=o["discount_value"],
                min_cart_value=o["min_cart_value"],
                max_discount_cap=o["max_discount_cap"],
                is_active=True
            ))

    db.commit()

    AuditService.log_financial_decision(
        db=db,
        actor="SYSTEM",
        action_type="GENESIS_SYSTEM_INITIALIZATION",
        payload={"merchant": "novatech", "products_count": len(products_data)},
        decision_rationale="AgentStore financial ledger initialized with cryptographic genesis block."
    )

if __name__ == "__main__":
    with SessionLocal() as session:
        seed_database(session)
        print("Database seeded successfully!")
