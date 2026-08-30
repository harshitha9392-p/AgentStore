const API_BASE = '/api/v1';

export const api = {
  getProducts: async () => {
    const res = await fetch(`${API_BASE}/catalog/products`);
    return res.json();
  },
  getCart: async (sessionId: string) => {
    const res = await fetch(`${API_BASE}/cart/${sessionId}`);
    return res.json();
  },
  addToCart: async (sessionId: string, productId: string, qty = 1, metadata = {}) => {
    const res = await fetch(`${API_BASE}/cart/items`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, product_id: productId, quantity: qty, metadata })
    });
    return res.json();
  },
  chat: async (sessionId: string, message: string) => {
    const res = await fetch(`${API_BASE}/agent/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, message })
    });
    return res.json();
  },
  getAuditLogs: async (limit = 20) => {
    const res = await fetch(`${API_BASE}/audit/logs?limit=${limit}`);
    return res.json();
  },
  verifyAuditChain: async () => {
    const res = await fetch(`${API_BASE}/audit/verify-chain`);
    return res.json();
  },
  getPolicyRules: async () => {
    const res = await fetch(`${API_BASE}/policies/rules`);
    return res.json();
  },
  runChaosScenario: async (scenario: string) => {
    const res = await fetch(`${API_BASE}/demo/scenarios/${scenario}`, { method: 'POST' });
    return res.json();
  },
  verifyRazorpayPayment: async (orderId: string, razorpayOrderId: string, paymentId: string, signature: string) => {
    const res = await fetch(`${API_BASE}/payments/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        order_id: orderId,
        razorpay_order_id: razorpayOrderId,
        razorpay_payment_id: paymentId,
        razorpay_signature: signature
      })
    });
    return res.json();
  }
};
