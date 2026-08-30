#!/usr/bin/env bash
set -e

BASE_URL="http://localhost:8000"

echo "================================================================="
echo "  AgentStore — Razorpay AI Buildathon 2026 (Track 01) Demo Script"
echo "================================================================="
echo ""

# 1. Health Check
echo "🔍 [1/6] Checking Platform Health..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# 2. Seed Catalog
echo "📦 [2/6] Seeding Merchant Catalog & Canonical Tools..."
curl -s -X POST "$BASE_URL/api/v1/demo/seed" | python3 -m json.tool
echo ""

# 3. Conversational AI Shopping Turn
echo "🤖 [3/6] Conversational Discovery & Add to Cart via AI Agent..."
SESSION="judge_demo_$(date +%s)"
curl -s -X POST "$BASE_URL/api/v1/agent/chat" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION\", \"message\": \"Find me noise canceling headphones under 35000\"}" | python3 -m json.tool
echo ""

# 4. Upsell & Bundle Evaluation
echo "🎁 [4/6] Evaluating Dynamic Bundle Offers & AOV Growth Tiers..."
curl -s "$BASE_URL/api/v1/offers/evaluate/$SESSION" | python3 -m json.tool
echo ""

# 5. Non-Bypassable Policy Gate Attack Defense
echo "🛡️ [5/6] Testing Non-Bypassable Policy Gate Against 90% Promo Exploit..."
curl -s -X POST "$BASE_URL/api/v1/demo/scenarios/prompt-injection" | python3 -m json.tool
echo ""

# 6. Immutable SHA-256 Audit Verification
echo "🔐 [6/6] Verifying Cryptographic SHA-256 Audit Ledger Chain..."
curl -s "$BASE_URL/api/v1/audit/verify-chain" | python3 -m json.tool
echo ""

echo "================================================================="
echo "  ✅ All AgentStore Core Capabilities Successfully Demonstrated!"
echo "  🌐 Access the interactive dashboard at: http://localhost:8000"
echo "================================================================="
