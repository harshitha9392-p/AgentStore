import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import { Product, Cart, AuditBlock, PolicyRule } from './types';

export default function App() {
  const [sessionId] = useState(() => 'sess_' + Math.random().toString(36).substring(2, 9));
  const [cart, setCart] = useState<Cart | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditBlock[]>([]);
  const [policyRules, setPolicyRules] = useState<PolicyRule[]>([]);
  const [messages, setMessages] = useState<Array<{ role: string; content: string; cards?: any[] }>>([
    {
      role: 'assistant',
      content: '👋 Welcome to **AgentStore**! I am your AI Shopping & Growth Assistant powered by Razorpay. Ask me to find products, discover bundle savings, or checkout!'
    }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const refreshData = async () => {
    try {
      const [c, p, a, r] = await Promise.all([
        api.getCart(sessionId),
        api.getProducts(),
        api.getAuditLogs(10),
        api.getPolicyRules()
      ]);
      setCart(c);
      setProducts(p);
      setAuditLogs(a);
      setPolicyRules(r);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    refreshData();
  }, [sessionId]);

  const handleSend = async (customText?: string) => {
    const text = (customText || inputMsg).trim();
    if (!text) return;

    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setInputMsg('');
    setLoading(true);

    try {
      const res = await api.chat(sessionId, text);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply, cards: res.action_cards }]);
      await refreshData();
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Error communicating with agent.' }]);
    } finally {
      setLoading(false);
    }
  };

  const runScenario = async (sc: string) => {
    const res = await api.runChaosScenario(sc);
    alert(`🧪 Chaos Scenario Triggered:\n\n${res.resolution}\n\nDiagnostic: ${JSON.stringify(res, null, 2)}`);
    refreshData();
  };

  const verifyAudit = async () => {
    const res = await api.verifyAuditChain();
    alert(`🔐 SHA-256 Ledger Verification:\n\nValid: ${res.is_valid}\nVerified Blocks: ${res.verified_blocks}/${res.total_blocks}\nDetails: ${res.details}`);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header */}
      <header className="bg-slate-900/80 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between sticky top-0 z-50 backdrop-blur">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30">
            AS
          </div>
          <div>
            <h1 className="font-bold text-base tracking-tight">AgentStore</h1>
            <p className="text-[11px] text-slate-400">AI Growth & Agentic Commerce Platform · Razorpay Track 01</p>
          </div>
        </div>
        <div className="flex items-center space-x-3 text-xs">
          <span className="bg-emerald-950 border border-emerald-800 text-emerald-300 px-3 py-1 rounded-full">● Non-Bypassable Policy Gates Active</span>
          <span className="bg-indigo-950 border border-indigo-800 text-indigo-300 px-3 py-1 rounded-full">🔗 SHA-256 Chained Ledger</span>
        </div>
      </header>

      {/* Main Grid */}
      <div className="flex-1 grid grid-cols-12 gap-6 p-6 max-w-[1700px] w-full mx-auto">
        {/* Chat Section (6 Cols) */}
        <section className="col-span-12 lg:col-span-6 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col h-[calc(100vh-130px)] shadow-2xl overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-800 flex justify-between items-center bg-slate-900/90">
            <span className="text-xs font-semibold text-slate-300">Conversational Commerce Assistant</span>
            <span className="text-[10px] text-indigo-400 font-mono bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">Session: {sessionId}</span>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
            {messages.map((m, idx) => (
              <div key={idx} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-4 rounded-2xl ${m.role === 'user' ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-800/90 border border-slate-700 text-slate-200 rounded-tl-none'}`}>
                  <p className="whitespace-pre-line">{m.content}</p>
                </div>
              </div>
            ))}
            {loading && <div className="text-xs text-indigo-400 animate-pulse">Agent is thinking and querying tools...</div>}
          </div>

          <div className="p-4 border-t border-slate-800 bg-slate-900/90 flex gap-2">
            <input
              type="text"
              value={inputMsg}
              onChange={e => setInputMsg(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask for recommendations, add items to cart, apply promo..."
              className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
            <button onClick={() => handleSend()} className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-2.5 rounded-xl text-xs font-medium">Send</button>
          </div>
        </section>

        {/* Dashboard Tools (6 Cols) */}
        <section className="col-span-12 lg:col-span-6 flex flex-col space-y-6 h-[calc(100vh-130px)] overflow-y-auto pr-1">
          {/* Cart Widget */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h2 className="font-bold text-sm text-slate-200 pb-2 border-b border-slate-800 flex justify-between">
              <span>Shopping Cart & Authoritative Pricing</span>
              <span className="text-xs text-indigo-400">{cart?.item_count || 0} items</span>
            </h2>
            <div className="my-3 space-y-2 max-h-36 overflow-y-auto text-xs">
              {cart?.items.map(it => (
                <div key={it.id} className="flex justify-between py-1.5 border-b border-slate-800">
                  <span>{it.quantity}x {it.product_name}</span>
                  <span className="font-bold">₹{it.total_price.toLocaleString('en-IN')}</span>
                </div>
              ))}
              {(!cart?.items || cart.items.length === 0) && <p className="text-slate-500 py-2">Cart is empty.</p>}
            </div>
            <div className="bg-slate-950 p-3 rounded-xl text-xs space-y-1">
              <div className="flex justify-between text-slate-400"><span>Subtotal:</span><span>₹{cart?.subtotal?.toLocaleString('en-IN') || '0.00'}</span></div>
              <div className="flex justify-between text-emerald-400"><span>Discount:</span><span>-₹{cart?.discount_amount?.toLocaleString('en-IN') || '0.00'}</span></div>
              <div className="flex justify-between font-bold text-white text-sm pt-1 border-t border-slate-800"><span>Total:</span><span>₹{cart?.total_amount?.toLocaleString('en-IN') || '0.00'}</span></div>
            </div>
          </div>

          {/* Chaos Simulator */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
            <h2 className="font-bold text-sm text-amber-400 pb-2 border-b border-slate-800">Buildathon Scenario Simulator</h2>
            <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
              <button onClick={() => runScenario('stock-out')} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-2.5 rounded-xl text-left text-rose-400 font-semibold">1. Stock-Out Race</button>
              <button onClick={() => runScenario('prompt-injection')} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-2.5 rounded-xl text-left text-amber-400 font-semibold">2. 90% Promo Exploit</button>
              <button onClick={() => runScenario('price-hallucination')} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-2.5 rounded-xl text-left text-cyan-400 font-semibold">3. Price Hallucination</button>
              <button onClick={() => runScenario('payment-tamper')} className="bg-slate-800 hover:bg-slate-700 border border-slate-700 p-2.5 rounded-xl text-left text-indigo-400 font-semibold">4. Signature Tamper</button>
            </div>
          </div>

          {/* Audit Ledger */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex-1 flex flex-col">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h2 className="font-bold text-sm text-emerald-400">SHA-256 Audit Trail</h2>
              <button onClick={verifyAudit} className="text-xs bg-emerald-950 text-emerald-300 border border-emerald-700 px-2.5 py-1 rounded-lg">Verify Chain</button>
            </div>
            <div className="mt-3 space-y-2 text-[11px] font-mono overflow-y-auto max-h-40">
              {auditLogs.map(l => (
                <div key={l.id} className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                  <div className="flex justify-between text-indigo-400 font-bold">
                    <span>#{l.sequence_index} [{l.action_type}]</span>
                    <span className="text-slate-500">{new Date(l.timestamp).toLocaleTimeString()}</span>
                  </div>
                  <p className="text-slate-400 font-sans mt-0.5">{l.decision_rationale}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
