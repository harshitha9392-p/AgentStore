export interface Product {
  id: string;
  sku: string;
  name: string;
  slug: string;
  category_name?: string;
  category_slug?: string;
  description: string;
  brand?: string;
  base_price: number;
  compare_at_price?: number;
  currency: string;
  stock_quantity: number;
  is_available: boolean;
  tags: string[];
  attributes: Record<string, any>;
  image_url?: string;
  rating: number;
  review_count: number;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  sku: string;
  unit_price: number;
  quantity: number;
  total_price: number;
  image_url?: string;
  item_metadata?: Record<string, any>;
}

export interface Cart {
  id: string;
  session_id: string;
  status: string;
  items: CartItem[];
  item_count: number;
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  currency: string;
  applied_coupon?: string;
  applied_offers?: any[];
}

export interface AuditBlock {
  id: string;
  sequence_index: number;
  timestamp: string;
  session_id?: string;
  order_id?: string;
  actor: string;
  action_type: string;
  payload: Record<string, any>;
  decision_rationale?: string;
  previous_hash: string;
  block_hash: string;
}

export interface PolicyRule {
  id: string;
  name: string;
  description?: string;
  rule_type: string;
  threshold_value?: number;
  action: string;
  is_active: boolean;
}
