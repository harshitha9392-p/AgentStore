from typing import Optional, Dict, Any

class AgentStoreException(Exception):
    def __init__(self, message: str, code: str = "GENERIC_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class PolicyViolationException(AgentStoreException):
    def __init__(self, message: str, policy_name: str, requested_value: Any, allowed_limit: Any, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details.update({
            "policy_name": policy_name,
            "requested_value": requested_value,
            "allowed_limit": allowed_limit
        })
        super().__init__(message=message, code="POLICY_VIOLATION", details=details)

class PriceHallucinationException(AgentStoreException):
    def __init__(self, message: str, item_id: str, claimed_price: float, authoritative_price: float):
        details = {
            "item_id": item_id,
            "claimed_price": claimed_price,
            "authoritative_price": authoritative_price,
            "price_delta": claimed_price - authoritative_price
        }
        super().__init__(message=message, code="PRICE_HALLUCINATION_DETECTED", details=details)

class StockUnavailableException(AgentStoreException):
    def __init__(self, message: str, product_id: str, requested_qty: int, available_stock: int, suggested_alternatives: Optional[list] = None):
        details = {
            "product_id": product_id,
            "requested_qty": requested_qty,
            "available_stock": available_stock,
            "suggested_alternatives": suggested_alternatives or []
        }
        super().__init__(message=message, code="STOCK_UNAVAILABLE", details=details)

class HumanApprovalRequiredException(AgentStoreException):
    def __init__(self, message: str, order_id: str, total_amount: float, threshold: float):
        details = {
            "order_id": order_id,
            "total_amount": total_amount,
            "threshold": threshold,
            "status": "REQUIRES_MERCHANT_APPROVAL"
        }
        super().__init__(message=message, code="HUMAN_APPROVAL_REQUIRED", details=details)

class PaymentVerificationException(AgentStoreException):
    def __init__(self, message: str, razorpay_order_id: str, razorpay_payment_id: Optional[str] = None):
        details = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id
        }
        super().__init__(message=message, code="PAYMENT_VERIFICATION_FAILED", details=details)
