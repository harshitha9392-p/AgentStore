from typing import List, Dict, Any

AGENT_TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "search_catalog",
        "description": "Searches merchant products by natural language query, category, price range, and stock availability.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword e.g. 'wireless headphones', 'laptop sleeve', 'running shoes'"
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter slug e.g. 'electronics', 'apparel', 'accessories'"
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum price in INR"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price in INR"
                },
                "in_stock_only": {
                    "type": "boolean",
                    "description": "Whether to return only items in stock (default true)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_product_details",
        "description": "Retrieves comprehensive details, specifications, price, and real-time inventory for a specific product ID or SKU.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id_or_sku": {
                    "type": "string",
                    "description": "Unique product ID or SKU code"
                }
            },
            "required": ["product_id_or_sku"]
        }
    },
    {
        "name": "add_to_cart",
        "description": "Adds a product to the user's active shopping cart with specified quantity and bundle metadata.",
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID to add"
                },
                "quantity": {
                    "type": "integer",
                    "description": "Quantity (default 1)"
                },
                "bundle_discount_pct": {
                    "type": "number",
                    "description": "Optional approved bundle discount percentage if part of an upsell rule"
                }
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "get_cart",
        "description": "Retrieves current active shopping cart items, item count, subtotal, applied discounts, and total amount.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "recommend_bundles_and_upsells",
        "description": "Calculates personalized bundle cross-sells and tiered spending discounts based on the current cart.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "apply_coupon",
        "description": "Applies a promotional or dynamic discount coupon code to the shopping cart.",
        "parameters": {
            "type": "object",
            "properties": {
                "coupon_code": {
                    "type": "string",
                    "description": "Coupon code to apply e.g. 'SAVE10', 'FESTIVE20', 'WELCOME100'"
                }
            },
            "required": ["coupon_code"]
        }
    },
    {
        "name": "initiate_checkout",
        "description": "Runs server-side policy gates and generates a Razorpay Order ID for payment.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer full name"
                },
                "customer_email": {
                    "type": "string",
                    "description": "Customer email address"
                },
                "customer_phone": {
                    "type": "string",
                    "description": "Customer mobile phone number"
                },
                "shipping_address": {
                    "type": "string",
                    "description": "Full delivery address"
                }
            },
            "required": ["customer_name", "customer_email"]
        }
    }
]
