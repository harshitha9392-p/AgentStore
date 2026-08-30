import re
import json
import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.agent.tools import AGENT_TOOLS_DEFINITIONS
from backend.app.agent.prompt_templates import COMMERCE_AGENT_SYSTEM_PROMPT

class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        pass

class MockDeterministicLLM(BaseLLMAdapter):
    """
    Intelligent built-in fallback agent that operates 100% offline without requiring API keys.
    Handles natural language understanding for search, recommendation, bundle upsell, cart management, and checkout.
    """
    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        last_msg = messages[-1]["content"].lower() if messages else ""
        tool_calls = []
        content = ""

        # 1. Prompt Injection / Exploit Detection
        if any(w in last_msg for w in ["ignore previous", "admin override", "90% discount", "free laptop", "give me 99% off"]):
            return {
                "content": "🛡️ **Policy Gate Security Warning**: I cannot apply arbitrary or unauthorized discounts. All discounts must comply with strict merchant policy ceilings (maximum 25% discount cap). Would you like me to check available authorized promo codes like `SAVE10` or `FESTIVE20` instead?",
                "tool_calls": []
            }

        # 2. Checkout Intent
        if any(w in last_msg for w in ["checkout", "pay now", "buy now", "place order", "complete purchase"]):
            tool_calls.append({
                "name": "initiate_checkout",
                "arguments": {
                    "customer_name": "Valued Shopper",
                    "customer_email": "shopper@buildathon.razorpay.com",
                    "customer_phone": "+919876543210",
                    "shipping_address": "Flat 402, Innovators Residency, Bangalore 560001"
                }
            })
            content = "I'm initiating the server-side policy verification and generating your Razorpay checkout details now..."

        # 3. Apply Coupon Intent
        elif any(w in last_msg for w in ["apply coupon", "coupon", "promo", "discount code"]):
            match = re.search(r'\b(save10|festive20|welcome100|vip25|[a-z0-9]{4,10})\b', last_msg)
            code = match.group(1).upper() if match else "SAVE10"
            tool_calls.append({
                "name": "apply_coupon",
                "arguments": {"coupon_code": code}
            })
            content = f"Validating and applying promo code **{code}** to your cart..."

        # 4. View Cart Intent
        elif any(w in last_msg for w in ["view cart", "show cart", "my cart", "what is in my cart", "cart items"]):
            tool_calls.append({
                "name": "get_cart",
                "arguments": {}
            })
            content = "Here is your current shopping cart breakdown:"

        # 5. Add to Cart Intent
        elif any(w in last_msg for w in ["add to cart", "buy this", "add macbook", "add headphones", "add bag", "add item", "add"]):
            query = ""
            for term in ["macbook", "headphone", "headphones", "sony", "boat", "sleeve", "mouse", "charger", "backpack", "jacket", "drone"]:
                if term in last_msg:
                    query = term
                    break
            
            tool_calls.append({
                "name": "search_catalog",
                "arguments": {"query": query or "", "limit": 3}
            })
            content = "Searching the catalog and checking real-time inventory..."

        # 6. Recommendation / Deals / Upsell Intent
        elif any(w in last_msg for w in ["recommend", "upsell", "bundle", "deals", "offer", "discount"]):
            tool_calls.append({
                "name": "recommend_bundles_and_upsells",
                "arguments": {}
            })
            content = "I found these personalized bundle cross-sell discounts and spending reward tiers for you:"

        # 7. General Search / Discovery Intent
        else:
            # Extract keywords and price limits
            price_match = re.search(r'(?:under|below|less than|max)\s*(?:rs\.?|inr|₹)?\s*(\d+)', last_msg)
            max_price = float(price_match.group(1)) if price_match else None

            # Extract main product terms
            keyword = ""
            for term in ["headphone", "headphones", "laptop", "macbook", "xps", "mouse", "sleeve", "charger", "backpack", "drone", "audio", "wearable"]:
                if term in last_msg:
                    keyword = term
                    break

            if not keyword:
                # Clean prompt
                keyword = last_msg.replace("find", "").replace("search", "").replace("show", "").replace("for", "").replace("me", "").replace("under", "").replace("below", "").strip()

            args: Dict[str, Any] = {"query": keyword, "limit": 4}
            if max_price:
                args["max_price"] = max_price

            tool_calls.append({
                "name": "search_catalog",
                "arguments": args
            })
            content = f"Here are the top matches found in the merchant catalog:"

        return {
            "content": content,
            "tool_calls": tool_calls
        }

class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key:
            mock = MockDeterministicLLM()
            return await mock.generate_response_with_tools(messages, tools)

        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            contents = []
            for m in messages:
                role = "user" if m.get("role") in ["user", "system"] else "model"
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

            payload = {
                "contents": contents,
                "systemInstruction": {"parts": [{"text": COMMERCE_AGENT_SYSTEM_PROMPT}]}
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    cand = data.get("candidates", [{}])[0]
                    text = cand.get("content", {}).get("parts", [{}])[0].get("text", "")
                    return {"content": text, "tool_calls": []}
        except Exception:
            pass

        mock = MockDeterministicLLM()
        return await mock.generate_response_with_tools(messages, tools)

class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_response_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not self.api_key:
            mock = MockDeterministicLLM()
            return await mock.generate_response_with_tools(messages, tools)

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "system", "content": COMMERCE_AGENT_SYSTEM_PROMPT}] + messages
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    msg = data["choices"][0]["message"]
                    return {"content": msg.get("content", ""), "tool_calls": []}
        except Exception:
            pass

        mock = MockDeterministicLLM()
        return await mock.generate_response_with_tools(messages, tools)

def get_llm_adapter() -> BaseLLMAdapter:
    provider = (settings.AGENT_PROVIDER or "mock").lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiAdapter(api_key=settings.GEMINI_API_KEY)
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIAdapter(api_key=settings.OPENAI_API_KEY)
    else:
        return MockDeterministicLLM()
