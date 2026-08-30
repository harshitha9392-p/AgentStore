# AgentStore: Autonomous AI Growth & Agentic Commerce Platform

[![Track](https://img.shields.io/badge/Razorpay_Buildathon_2026-Track_01:_AI_Growth_%26_Agentic_Commerce-blue?style=for-the-badge)](https://razorpay.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://sqlalchemy.org)
[![Razorpay](https://img.shields.io/badge/Razorpay-Test_Mode_API-0C2340?style=for-the-badge&logo=razorpay&logoColor=white)](https://razorpay.com/docs)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> **AgentStore** converts arbitrary merchant catalogs into an agent-readable canonical schema, powers a conversational shopping assistant that drives Average Order Value (AOV) via dynamic bundle cross-sells, enforces **non-bypassable server-side policy gates**, logs all financial decisions in an **immutable SHA-256 cryptographic audit trail**, and provides seamless **Razorpay test mode checkout**.

---

## 🌟 Key Pillars & Capabilities

### 1. Canonical Schema & Dynamic Tool Layer
- **Arbitrary Catalog Ingestion**: Imports raw JSON, CSV, and Shopify-formatted product lists into standard canonical models.
- **Canonical Agent Tools**: Exposes `search_catalog`, `get_product_details`, `add_to_cart`, `recommend_bundles_and_upsells`, `apply_coupon`, and `initiate_checkout` for tool-calling agents.

### 2. Conversational Shopping & Pluggable Agent
- **Universal Provider Architecture**: Operates with a high-fidelity **Built-in Deterministic Agent** out of the box (zero API key needed), with pluggable adapters for **Google Gemini**, **Anthropic Claude**, and **OpenAI**.
- **Generative UI Action Cards**: Rich interactive widgets rendered directly in chat for product carousels, bundle offers, and checkout prompts.

### 3. AOV Growth & Offer Engine
- **Intelligent Bundle Upsells**: Suggests complementary items with pre-calculated bundle discounts (e.g., Laptop + Sleeve at 15% off).
- **Spending Reward Tiers**: Dynamically calculates progress toward tiered discounts (e.g. *"Add items worth ₹500 more to unlock 20% discount"*).

### 4. Non-Bypassable Server-Side Policy Gates
The AI Agent **NEVER** decides final pricing or charges money directly. Every transaction must pass 5 server-side security gates:
- **Price Integrity Gate**: Verifies item prices against authoritative PostgreSQL records at checkout time (detects and halts price hallucinations).
- **Max Discount % Ceiling**: Hard limit enforcing that total discounts cannot exceed merchant margins (e.g., strictly ≤ 25%).
- **Max Order Value Cap**: Enforces single-order transaction ceiling.
- **Category Restriction Gate**: Blocks restricted or age-gated merchandise from automated checkout.
- **Human-in-the-Loop (HITL) Threshold**: Escalates high-value orders (> ₹10,000) to merchant approval before Razorpay Order generation.

### 5. Immutable SHA-256 Cryptographic Audit Ledger
- Every discount proposal, policy evaluation, order initialization, and Razorpay payment verification is recorded in an append-only ledger where `block_hash = SHA256(previous_hash + timestamp + actor + action + payload)`.
- Verification endpoint `/api/v1/audit/verify-chain` mathematically proves ledger integrity and detects any database tampering.

### 6. Built-in Chaos & Failure Simulator
Interactive simulation and graceful recovery for:
- **Stock-Out Race Conditions** (Agent catches inventory drops and suggests in-stock substitutes).
- **Prompt Injection 90% Discount Exploits** (Intercepted and blocked by server policy gates).
- **Price Hallucination Attempts** (Authoritative DB price lock blocks discrepancies).
- **Payment Signature Tampering** (HMAC-SHA256 verification catches fraudulent signatures).

---

## 🏗️ System Architecture

```
                                  +---------------------------------------+
                                  |     Shopper & Merchant Dashboard      |
                                  |   (React + TypeScript + Tailwind)     |
                                  +-------------------+-------------------+
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |           FastAPI Gateway             |
                                  +-------------------+-------------------+
                                                      |
                  +-----------------------------------+-----------------------------------+
                  |                                   |                                   |
                  v                                   v                                   v
+-----------------------------------+ +-----------------------------------+ +-----------------------------------+
|     Autonomous Agent Engine       | |   Non-Bypassable Policy Gates     | |  Immutable Cryptographic Ledger   |
| - Pluggable (Mock/Gemini/Claude)  | | - DB Price Integrity Lock         | | - SHA-256 Chained Hash Blocks     |
| - Multi-turn Memory & Tool Layer  | | - Max Discount % Ceiling (25%)    | | - Tamper-Proof Audit History      |
| - AOV Upsell & Bundle Builder     | | - HITL High-Value Approval Queue  | | - Real-Time Chain Verifier        |
+-----------------+-----------------+ +-----------------+-----------------+ +-----------------+-----------------+
                  |                                     |                                     |
                  +-------------------------------------+-------------------------------------+
                                                        |
                                                        v
                                  +---------------------------------------+
                                  |      Razorpay Test Mode Engine        |
                                  |  - Orders API (/v1/orders in paise)   |
                                  |  - HMAC-SHA256 Signature Verification |
                                  |  - Webhook Authentication             |
                                  +-------------------+-------------------+
                                                      |
                                      +---------------+---------------+
                                      |                               |
                                      v                               v
                              +---------------+               +---------------+
                              |  PostgreSQL   |               | Redis Session |
                              |  (Catalog/DB) |               |  (Cart/State) |
                              +---------------+               +---------------+
```

---

## 🚀 Quick Start Guide

### Option 1: One-Command Docker Compose (Recommended)
```bash
# Clone and enter directory
cd agentstore

# Start all services (Backend, Frontend, PostgreSQL, Redis)
docker compose up --build
```
- **Web UI**: Open `http://localhost:3000` (or `http://localhost:8000`)
- **API Swagger Docs**: Open `http://localhost:8000/docs`

---

### Option 2: Local Python Run (Zero External Dependencies)
```bash
cd agentstore

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Start backend server
uvicorn backend.app.main:app --port 8000 --reload
```
Open `http://localhost:8000` in your web browser.

---

## 🧪 Running Automated Tests

Run the complete test suite verifying all 6 core pillars:
```bash
PYTHONPATH=. .venv/bin/pytest backend/tests -v
```

---

## 💻 REST API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck and engine configuration |
| `POST` | `/api/v1/agent/chat` | Multi-turn conversational AI shopping turn |
| `GET` | `/api/v1/catalog/products` | Search catalog with keyword, category, and price filters |
| `POST` | `/api/v1/catalog/import` | Import raw merchant catalog to canonical schema |
| `GET` | `/api/v1/cart/{session_id}` | Retrieve active cart and authoritative subtotal |
| `POST` | `/api/v1/cart/items` | Add product to cart with bundle discount metadata |
| `POST` | `/api/v1/cart/apply-coupon` | Apply policy-bounded promo code to cart |
| `GET` | `/api/v1/offers/evaluate/{session_id}` | Calculate cross-sell bundles & AOV reward tiers |
| `POST` | `/api/v1/orders/checkout` | Policy-gated checkout & Razorpay order generation |
| `POST` | `/api/v1/orders/approval` | Merchant Human-in-the-loop decision (APPROVED/REJECTED) |
| `POST` | `/api/v1/payments/verify` | HMAC-SHA256 Razorpay payment verification & fulfillment |
| `GET` | `/api/v1/audit/logs` | Query immutable financial audit ledger |
| `GET` | `/api/v1/audit/verify-chain` | Cryptographic SHA-256 chain verification endpoint |
| `POST` | `/api/v1/demo/scenarios/{type}` | Trigger failure & attack simulations (stockout, injection, price tampering) |

---

## 🎬 Presentation & Demonstration
For full judging instructions, see [demo/DEMO_SCRIPT.md](demo/DEMO_SCRIPT.md) or run:
```bash
./demo/run_demo_scenarios.sh
```
