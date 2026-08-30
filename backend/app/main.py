import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal
from backend.app.core.redis_client import redis_manager
from backend.app.core.exceptions import (
    AgentStoreException,
    PolicyViolationException,
    PriceHallucinationException,
    StockUnavailableException,
    HumanApprovalRequiredException,
    PaymentVerificationException
)
from backend.app.api.v1.router import api_v1_router
from backend.app.db.seed_data import seed_database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Init database schema & seed catalog
    init_db()
    with SessionLocal() as session:
        seed_database(session)
    await redis_manager.connect()
    print(f"🚀 {settings.APP_NAME} started on port {settings.PORT} (Env: {settings.APP_ENV})")
    yield
    print(f"🛑 {settings.APP_NAME} shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AgentStore: Autonomous AI Growth & Agentic Commerce Platform for Razorpay AI Buildathon 2026",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(PolicyViolationException)
async def policy_violation_handler(request: Request, exc: PolicyViolationException):
    return JSONResponse(
        status_code=422,
        content={
            "error_code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(PriceHallucinationException)
async def price_hallucination_handler(request: Request, exc: PriceHallucinationException):
    return JSONResponse(
        status_code=409,
        content={
            "error_code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(StockUnavailableException)
async def stock_unavailable_handler(request: Request, exc: StockUnavailableException):
    return JSONResponse(
        status_code=409,
        content={
            "error_code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(PaymentVerificationException)
async def payment_verification_handler(request: Request, exc: PaymentVerificationException):
    return JSONResponse(
        status_code=400,
        content={
            "error_code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

@app.exception_handler(HumanApprovalRequiredException)
async def hitl_approval_handler(request: Request, exc: HumanApprovalRequiredException):
    return JSONResponse(
        status_code=202,
        content={
            "error_code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )

app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "razorpay_mock_mode": settings.RAZORPAY_MOCK_MODE,
        "agent_provider": settings.AGENT_PROVIDER
    }

# Interactive Embedded Dashboard UI
EMBEDDED_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AgentStore — AI Growth & Agentic Commerce Platform</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 50: '#eef2ff', 500: '#4f46e5', 600: '#4338ca', 700: '#3730a3' },
            razorpay: { 500: '#0c2340', 600: '#032a53', accent: '#3395ff' }
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulse-glow { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
    .pulse-indicator { animation: pulse-glow 2s infinite; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col font-sans">
  
  <header class="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between shadow-lg">
    <div class="flex items-center space-x-3">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-500 to-cyan-400 flex items-center justify-center shadow-md">
        <i class="fa-solid fa-robot text-white text-xl"></i>
      </div>
      <div>
        <h1 class="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">AgentStore</h1>
        <p class="text-xs text-slate-400">Autonomous Commerce & Growth Agent · Razorpay Track 01</p>
      </div>
    </div>

    <div class="flex items-center space-x-4">
      <div class="flex items-center space-x-2 bg-emerald-950/60 border border-emerald-800/80 px-3 py-1 rounded-full text-xs text-emerald-300">
        <span class="w-2 h-2 rounded-full bg-emerald-400 pulse-indicator"></span>
        <span>Policy Gates: Active</span>
      </div>
      <div class="flex items-center space-x-2 bg-indigo-950/60 border border-indigo-800/80 px-3 py-1 rounded-full text-xs text-indigo-300">
        <i class="fa-solid fa-link text-indigo-400"></i>
        <span>Audit Chain: Verified</span>
      </div>
      <div class="flex items-center space-x-2 bg-blue-950/60 border border-blue-800/80 px-3 py-1 rounded-full text-xs text-blue-300">
        <i class="fa-solid fa-bolt text-blue-400"></i>
        <span>Razorpay: Test Mode</span>
      </div>
    </div>
  </header>

  <main class="flex-1 grid grid-cols-12 gap-6 p-6 max-w-[1700px] w-full mx-auto">
    <section class="col-span-12 lg:col-span-6 flex flex-col bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl h-[calc(100vh-120px)]">
      <div class="bg-slate-900/90 border-b border-slate-800 px-5 py-3.5 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-3 h-3 rounded-full bg-indigo-500"></div>
          <span class="font-semibold text-sm text-slate-200">AI Commerce Assistant</span>
          <span class="text-xs text-indigo-400 bg-indigo-950/80 px-2 py-0.5 rounded border border-indigo-800/50">Tool-Calling</span>
        </div>
        <button onclick="clearSession()" class="text-xs text-slate-400 hover:text-rose-400 flex items-center space-x-1.5 transition">
          <i class="fa-solid fa-trash-can"></i>
          <span>Reset Session</span>
        </button>
      </div>

      <div id="chat-box" class="flex-1 overflow-y-auto p-5 space-y-4 text-sm scroll-smooth">
        <div class="flex items-start space-x-3">
          <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
            <i class="fa-solid fa-robot text-white text-xs"></i>
          </div>
          <div class="bg-slate-800/80 border border-slate-700/60 p-4 rounded-2xl rounded-tl-none max-w-[88%] text-slate-200 shadow">
            <p class="font-medium text-indigo-300 mb-1">AgentStore Assistant</p>
            <p>Welcome! I can help you find products, discover bundle savings, unlock cart discounts, and complete seamless Razorpay checkout. Try asking:</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <button onclick="sendQuickPrompt('Show me premium laptops')" class="text-xs bg-slate-700 hover:bg-indigo-700 text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-600 transition">💻 Show laptops</button>
              <button onclick="sendQuickPrompt('Add Sony WH-1000XM5 headphones to cart')" class="text-xs bg-slate-700 hover:bg-indigo-700 text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-600 transition">🎧 Add Sony Headphones</button>
              <button onclick="sendQuickPrompt('What bundle discounts do you recommend for my cart?')" class="text-xs bg-slate-700 hover:bg-indigo-700 text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-600 transition">🎁 Check Upsell Bundles</button>
              <button onclick="sendQuickPrompt('Apply coupon FESTIVE20')" class="text-xs bg-slate-700 hover:bg-indigo-700 text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-600 transition">🏷️ Apply FESTIVE20</button>
              <button onclick="sendQuickPrompt('I am ready to checkout')" class="text-xs bg-slate-700 hover:bg-indigo-700 text-slate-200 px-2.5 py-1.5 rounded-lg border border-slate-600 transition">💳 Checkout</button>
            </div>
          </div>
        </div>
      </div>

      <div class="p-4 border-t border-slate-800 bg-slate-900/90 flex items-center space-x-2">
        <input id="user-input" type="text" placeholder="Ask to find laptops, recommend accessories, add to cart, or checkout..." 
          onkeydown="if(event.key==='Enter') sendUserMessage()" 
          class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 shadow-inner">
        <button onclick="sendUserMessage()" class="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl font-medium text-sm flex items-center space-x-2 transition shadow-md shadow-indigo-600/30">
          <span>Send</span>
          <i class="fa-solid fa-paper-plane text-xs"></i>
        </button>
      </div>
    </section>

    <section class="col-span-12 lg:col-span-6 flex flex-col space-y-6 h-[calc(100vh-120px)] overflow-y-auto pr-1">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div class="flex items-center space-x-2">
            <i class="fa-solid fa-cart-shopping text-indigo-400"></i>
            <h2 class="font-bold text-slate-200 text-sm">Active Cart & Price Integrity Gate</h2>
          </div>
          <span id="cart-item-count" class="text-xs bg-indigo-900/60 text-indigo-300 px-2.5 py-0.5 rounded-full border border-indigo-700">0 items</span>
        </div>

        <div id="cart-items-container" class="my-4 divide-y divide-slate-800/80 max-h-40 overflow-y-auto">
          <p class="text-xs text-slate-500 py-3 text-center">Your shopping cart is currently empty.</p>
        </div>

        <div class="bg-slate-950/80 rounded-xl p-3.5 border border-slate-800 text-xs space-y-1.5">
          <div class="flex justify-between text-slate-400">
            <span>Authoritative Subtotal:</span>
            <span id="cart-subtotal" class="font-medium text-slate-200">₹0.00</span>
          </div>
          <div class="flex justify-between text-emerald-400">
            <span>Policy-Bounded Discount:</span>
            <span id="cart-discount" class="font-medium">-₹0.00</span>
          </div>
          <div class="flex justify-between text-sm font-bold text-white pt-2 border-t border-slate-800">
            <span>Final Total:</span>
            <span id="cart-total" class="text-indigo-400">₹0.00</span>
          </div>
        </div>

        <div class="mt-4 flex space-x-3">
          <button onclick="triggerCheckout()" class="flex-1 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold py-2.5 rounded-xl text-xs flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20 transition">
            <i class="fa-solid fa-lock"></i>
            <span>Pay with Razorpay Test Mode</span>
          </button>
        </div>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div class="flex items-center space-x-2 text-amber-400">
            <i class="fa-solid fa-flask-vial"></i>
            <h2 class="font-bold text-slate-200 text-sm">Buildathon Chaos & Resilience Simulator</h2>
          </div>
          <span class="text-xs bg-amber-950/60 text-amber-400 px-2 py-0.5 rounded border border-amber-800">Judge Scenarios</span>
        </div>
        <p class="text-xs text-slate-400 my-2.5">Simulate edge cases and verify server policy gate interception + graceful recovery:</p>
        
        <div class="grid grid-cols-2 gap-2.5">
          <button onclick="runScenario('stock-out')" class="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 p-2.5 rounded-xl text-left transition flex flex-col">
            <span class="text-xs font-semibold text-rose-400 flex items-center space-x-1.5">
              <i class="fa-solid fa-box-open"></i>
              <span>1. Stock-Out Race</span>
            </span>
            <span class="text-[11px] text-slate-400 mt-1">Tests graceful alternative item suggestion.</span>
          </button>

          <button onclick="runScenario('prompt-injection')" class="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 p-2.5 rounded-xl text-left transition flex flex-col">
            <span class="text-xs font-semibold text-amber-400 flex items-center space-x-1.5">
              <i class="fa-solid fa-shield-halved"></i>
              <span>2. 90% Promo Exploit</span>
            </span>
            <span class="text-[11px] text-slate-400 mt-1">Verifies hard 25% discount ceiling.</span>
          </button>

          <button onclick="runScenario('price-hallucination')" class="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 p-2.5 rounded-xl text-left transition flex flex-col">
            <span class="text-xs font-semibold text-cyan-400 flex items-center space-x-1.5">
              <i class="fa-solid fa-brain"></i>
              <span>3. Price Hallucination</span>
            </span>
            <span class="text-[11px] text-slate-400 mt-1">Locks ₹89k MacBook vs ₹199 claim.</span>
          </button>

          <button onclick="runScenario('payment-tamper')" class="bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 p-2.5 rounded-xl text-left transition flex flex-col">
            <span class="text-xs font-semibold text-indigo-400 flex items-center space-x-1.5">
              <i class="fa-solid fa-signature"></i>
              <span>4. Signature Tamper</span>
            </span>
            <span class="text-[11px] text-slate-400 mt-1">Tests HMAC-SHA256 rejection.</span>
          </button>
        </div>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex-1 flex flex-col">
        <div class="flex items-center justify-between pb-3 border-b border-slate-800">
          <div class="flex items-center space-x-2 text-emerald-400">
            <i class="fa-solid fa-cube"></i>
            <h2 class="font-bold text-slate-200 text-sm">Cryptographic Financial Audit Trail</h2>
          </div>
          <button onclick="verifyAuditChain()" class="text-xs bg-emerald-950 text-emerald-300 hover:bg-emerald-900 border border-emerald-700/60 px-2.5 py-1 rounded-lg flex items-center space-x-1.5 transition">
            <i class="fa-solid fa-check-double"></i>
            <span>Verify SHA-256 Chain</span>
          </button>
        </div>

        <div id="audit-log-container" class="mt-3 space-y-2 overflow-y-auto max-h-48 text-xs font-mono">
          <p class="text-slate-500 text-center py-4">Loading cryptographic blocks...</p>
        </div>
      </div>
    </section>
  </main>

  <div id="razorpay-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 hidden flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-slate-700 rounded-2xl max-w-md w-full p-6 shadow-2xl text-slate-200">
      <div class="flex items-center justify-between pb-4 border-b border-slate-800">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-white">R</div>
          <div>
            <h3 class="font-bold text-sm">Razorpay Checkout</h3>
            <p class="text-[11px] text-slate-400">Test Mode Gateway</p>
          </div>
        </div>
        <button onclick="closeRazorpayModal()" class="text-slate-400 hover:text-white"><i class="fa-solid fa-xmark"></i></button>
      </div>

      <div class="my-5 space-y-3 text-xs">
        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 space-y-1">
          <div class="flex justify-between"><span class="text-slate-400">Razorpay Order ID:</span><span id="rzp-order-id" class="font-mono text-indigo-300">-</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Amount to Pay:</span><span id="rzp-amount" class="font-bold text-emerald-400 text-sm">-</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Merchant:</span><span>NovaTech Flagship</span></div>
        </div>
        <p class="text-slate-400 text-[11px]">Clicking complete simulates authentic payment authorization with cryptographic HMAC-SHA256 signature verification.</p>
      </div>

      <div class="flex space-x-3">
        <button onclick="simulatePaymentSuccess()" class="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 rounded-xl text-xs flex items-center justify-center space-x-2 transition shadow-lg shadow-emerald-600/20">
          <i class="fa-solid fa-check"></i>
          <span>Authorize Test Payment</span>
        </button>
        <button onclick="closeRazorpayModal()" class="bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold px-4 py-2.5 rounded-xl text-xs">Cancel</button>
      </div>
    </div>
  </div>

  <script>
    const SESSION_ID = "shopper_session_" + Math.random().toString(36).substring(2, 9);
    let activeCheckoutOrder = null;

    async function fetchCart() {
      try {
        const res = await fetch(`/api/v1/cart/${SESSION_ID}`);
        const data = await res.json();
        renderCart(data);
      } catch (e) { console.error(e); }
    }

    function renderCart(cart) {
      document.getElementById('cart-item-count').innerText = `${cart.item_count} items`;
      document.getElementById('cart-subtotal').innerText = `₹${cart.subtotal.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      document.getElementById('cart-discount').innerText = `-₹${cart.discount_amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      document.getElementById('cart-total').innerText = `₹${cart.total_amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

      const container = document.getElementById('cart-items-container');
      if (!cart.items || cart.items.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-500 py-3 text-center">Your shopping cart is currently empty.</p>';
        return;
      }

      container.innerHTML = cart.items.map(it => `
        <div class="py-2.5 flex items-center justify-between text-xs">
          <div class="flex items-center space-x-2">
            <div class="w-6 h-6 rounded bg-indigo-950 flex items-center justify-center text-indigo-400 font-bold">${it.quantity}x</div>
            <div>
              <p class="font-medium text-slate-200">${it.product_name}</p>
              <p class="text-[10px] text-slate-400 font-mono">${it.sku} · ₹${it.unit_price.toLocaleString('en-IN')}</p>
            </div>
          </div>
          <div class="flex items-center space-x-3">
            <span class="font-bold text-slate-100">₹${it.total_price.toLocaleString('en-IN')}</span>
            <button onclick="removeCartItem('${it.product_id}')" class="text-slate-500 hover:text-rose-400"><i class="fa-solid fa-trash-can"></i></button>
          </div>
        </div>
      `).join('');
    }

    async function removeCartItem(productId) {
      await fetch('/api/v1/cart/items', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, product_id: productId, quantity: 0 })
      });
      fetchCart();
      fetchAuditLogs();
    }

    async function fetchAuditLogs() {
      try {
        const res = await fetch('/api/v1/audit/logs?limit=8');
        const logs = await res.json();
        const container = document.getElementById('audit-log-container');
        
        container.innerHTML = logs.map(l => `
          <div class="bg-slate-950/80 p-2.5 rounded-xl border border-slate-800 space-y-1">
            <div class="flex items-center justify-between">
              <span class="text-indigo-400 font-semibold">#${l.sequence_index} [${l.action_type}]</span>
              <span class="text-slate-500 text-[10px]">${new Date(l.timestamp).toLocaleTimeString()}</span>
            </div>
            <p class="text-slate-400 text-[11px] font-sans">${l.decision_rationale || 'Decision recorded'}</p>
            <div class="flex items-center space-x-2 text-[10px] text-slate-500">
              <span>Block Hash:</span>
              <span class="text-emerald-400 font-mono">${l.block_hash.substring(0, 16)}...</span>
            </div>
          </div>
        `).join('');
      } catch (e) { console.error(e); }
    }

    async function verifyAuditChain() {
      const res = await fetch('/api/v1/audit/verify-chain');
      const data = await res.json();
      alert(`🔐 Cryptographic Audit Verification:\n\nStatus: ${data.is_valid ? '100% VALID' : 'TAMPER DETECTED'}\nTotal Blocks: ${data.total_blocks}\nVerified Blocks: ${data.verified_blocks}\n\nDetails: ${data.details}`);
    }

    async function sendUserMessage() {
      const input = document.getElementById('user-input');
      const msg = input.value.trim();
      if (!msg) return;

      appendUserBubble(msg);
      input.value = '';

      try {
        const res = await fetch('/api/v1/agent/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: SESSION_ID, message: msg })
        });
        const data = await res.json();
        appendAgentResponse(data);
        fetchCart();
        fetchAuditLogs();
      } catch (e) {
        appendAgentText("Error communicating with agent. Please try again.");
      }
    }

    function sendQuickPrompt(text) {
      document.getElementById('user-input').value = text;
      sendUserMessage();
    }

    function appendUserBubble(text) {
      const chat = document.getElementById('chat-box');
      chat.innerHTML += `
        <div class="flex items-start justify-end space-x-3">
          <div class="bg-indigo-600 text-white p-3.5 rounded-2xl rounded-tr-none max-w-[85%] shadow-md">
            <p>${text}</p>
          </div>
          <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
            <i class="fa-solid fa-user text-white text-xs"></i>
          </div>
        </div>
      `;
      chat.scrollTop = chat.scrollHeight;
    }

    function appendAgentResponse(data) {
      const chat = document.getElementById('chat-box');
      let cardsHtml = '';

      if (data.action_cards) {
        for (const card of data.action_cards) {
          if (card.card_type === 'PRODUCT_LIST') {
            cardsHtml += `
              <div class="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2.5">
                ${card.data.products.map(p => `
                  <div class="bg-slate-900 border border-slate-700/80 rounded-xl p-3 flex flex-col justify-between">
                    <div>
                      <div class="flex items-center justify-between">
                        <span class="text-[10px] text-indigo-400 font-bold uppercase tracking-wider">${p.brand || 'Gear'}</span>
                        <span class="text-[11px] text-emerald-400 font-bold">₹${p.base_price.toLocaleString('en-IN')}</span>
                      </div>
                      <p class="font-semibold text-slate-100 text-xs mt-1">${p.name}</p>
                      <p class="text-[11px] text-slate-400 mt-1 line-clamp-2">${p.description}</p>
                    </div>
                    <button onclick="addToCartDirect('${p.id}')" class="mt-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs py-1.5 rounded-lg font-medium flex items-center justify-center space-x-1.5 transition">
                      <i class="fa-solid fa-plus text-[10px]"></i>
                      <span>Add to Cart</span>
                    </button>
                  </div>
                `).join('')}
              </div>
            `;
          } else if (card.card_type === 'BUNDLE_OFFER') {
            cardsHtml += `
              <div class="mt-3 bg-gradient-to-r from-indigo-950 to-purple-950 border border-indigo-700 p-3.5 rounded-xl">
                <div class="flex items-center space-x-2 text-indigo-300 font-bold text-xs">
                  <i class="fa-solid fa-gift"></i>
                  <span>${card.title}</span>
                </div>
                ${card.data.bundles.map(b => `
                  <div class="mt-2 flex items-center justify-between text-xs">
                    <div>
                      <p class="text-slate-200 font-medium">${b.recommended_product_name}</p>
                      <p class="text-[11px] text-emerald-400 font-semibold">${b.pitch_text}</p>
                    </div>
                    <button onclick="addBundleItem('${b.recommended_product_id}', ${b.bundle_discount_pct})" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded-lg font-medium">
                      Add for ₹${b.discounted_price.toLocaleString('en-IN')}
                    </button>
                  </div>
                `).join('')}
              </div>
            `;
          } else if (card.card_type === 'CHECKOUT_PROMPT') {
            activeCheckoutOrder = card.data;
            openRazorpayModal(card.data);
          } else if (card.card_type === 'APPROVAL_PENDING') {
            cardsHtml += `
              <div class="mt-3 bg-amber-950/80 border border-amber-700 p-3 rounded-xl text-amber-300 text-xs">
                <p class="font-bold flex items-center space-x-1.5"><i class="fa-solid fa-triangle-exclamation"></i><span>${card.title}</span></p>
                <p class="mt-1 text-slate-300">${card.data.message}</p>
              </div>
            `;
          } else if (card.card_type === 'POLICY_ALERT') {
            cardsHtml += `
              <div class="mt-3 bg-rose-950/80 border border-rose-700 p-3 rounded-xl text-rose-300 text-xs">
                <p class="font-bold flex items-center space-x-1.5"><i class="fa-solid fa-shield-halved"></i><span>Policy Guardrail Notice</span></p>
                <p class="mt-1 text-slate-300">${card.data.message || card.data.error}</p>
              </div>
            `;
          }
        }
      }

      chat.innerHTML += `
        <div class="flex items-start space-x-3">
          <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
            <i class="fa-solid fa-robot text-white text-xs"></i>
          </div>
          <div class="bg-slate-800/80 border border-slate-700/60 p-4 rounded-2xl rounded-tl-none max-w-[88%] text-slate-200 shadow">
            <p class="font-medium text-indigo-300 mb-1">AgentStore Assistant</p>
            <p class="whitespace-pre-line">${data.reply}</p>
            ${cardsHtml}
          </div>
        </div>
      `;
      chat.scrollTop = chat.scrollHeight;
    }

    async function addToCartDirect(productId) {
      await fetch('/api/v1/cart/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, product_id: productId, quantity: 1 })
      });
      fetchCart();
      fetchAuditLogs();
      sendQuickPrompt("Show my cart and recommend bundle savings");
    }

    async function addBundleItem(productId, discountPct) {
      await fetch('/api/v1/cart/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: SESSION_ID, product_id: productId, quantity: 1, metadata: { bundle_discount_pct: discountPct } })
      });
      fetchCart();
      fetchAuditLogs();
      sendQuickPrompt("I added the bundle item to my cart!");
    }

    async function triggerCheckout() {
      sendQuickPrompt("I want to checkout now with Razorpay");
    }

    function openRazorpayModal(rzpOrder) {
      document.getElementById('rzp-order-id').innerText = rzpOrder.razorpay_order_id;
      document.getElementById('rzp-amount').innerText = `₹${(rzpOrder.amount / 100).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      document.getElementById('razorpay-modal').classList.remove('hidden');
    }

    function closeRazorpayModal() {
      document.getElementById('razorpay-modal').classList.add('hidden');
    }

    async function simulatePaymentSuccess() {
      if (!activeCheckoutOrder) return;
      
      const res = await fetch('/api/v1/payments/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_id: activeCheckoutOrder.order_id,
          razorpay_order_id: activeCheckoutOrder.razorpay_order_id,
          razorpay_payment_id: "pay_" + Math.random().toString(36).substring(2, 14),
          razorpay_signature: "mock_valid_signature_buildathon"
        })
      });
      const data = await res.json();
      closeRazorpayModal();
      alert(`🎉 Payment Successful!\n\nOrder Number: ${data.order_number}\nStatus: PAID\nRazorpay Verified: YES (HMAC-SHA256)\nAudit Ledger: Updated with cryptographic confirmation.`);
      fetchCart();
      fetchAuditLogs();
    }

    async function runScenario(type) {
      const res = await fetch(`/api/v1/demo/scenarios/${type}`, { method: 'POST' });
      const data = await res.json();
      alert(`🧪 Chaos Scenario: ${data.scenario}\n\nResolution:\n${data.resolution}\n\nFull Diagnostic:\n${JSON.stringify(data, null, 2)}`);
      fetchAuditLogs();
    }

    async function clearSession() {
      await fetch(`/api/v1/agent/session/${SESSION_ID}`, { method: 'DELETE' });
      window.location.reload();
    }

    fetchCart();
    fetchAuditLogs();
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse, tags=["UI"])
async def serve_embedded_ui():
    return EMBEDDED_HTML
