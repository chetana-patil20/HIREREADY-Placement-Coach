import React, { useEffect, useRef, useState } from "react";
import { Send, Bot, User, Sparkles, RotateCcw, Wifi, WifiOff } from "lucide-react";
import Layout from "../components/Layout";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

const SUGGESTIONS = [
  "Am I ready for placements?",
  "What am I missing for my target role?",
  "Give me a 30-day placement plan.",
  "Why am I not eligible for a role I checked?",
  "How can I improve my interview score?",
];

export default function AICoach() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(true);
  const bottomRef = useRef(null);
  const { showToast } = useToast();

  useEffect(() => {
    api.get("/api/ai/chat/history")
      .then((res) => { setMessages(res.data); setConnected(true); })
      .catch((err) => { setConnected(false); showToast(err.response?.data?.detail || "AI Coach could not connect to the backend.", "error"); });
  }, []);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, loading]);

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || loading) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setLoading(true);
    try {
      const res = await api.post("/api/ai/chat", { message });
      setConnected(true);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.reply, mode: res.data.mode }]);
    } catch (err) {
      setConnected(false);
      const detail = err.response?.data?.detail || "The AI Coach request failed. Make sure the backend is running on port 8000.";
      setMessages((prev) => [...prev, { role: "assistant", content: detail, error: true }]);
    } finally { setLoading(false); }
  };

  const clearLocal = () => setMessages([]);

  return (
    <Layout title="AI placement coach" subtitle="Profile-aware coaching grounded in your actual readiness, skills and placement data.">
      <div className="card overflow-hidden ai-chat-shell">
        <div className="ai-header">
          <div className="flex items-center gap-3"><div className="ai-orb"><Sparkles size={18} /></div><div><h2 className="font-display font-semibold text-sm">HireReady Coach</h2><p className="text-xs text-muted">Deterministic placement facts + optional LLM coaching</p></div></div>
          <div className="flex items-center gap-2"><span className={`status-dot ${connected ? "online" : "offline"}`} /> <span className="text-xs text-muted">{connected ? "Backend connected" : "Connection issue"}</span><button className="icon-button" title="Clear visible chat" onClick={clearLocal}><RotateCcw size={15} /></button></div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-5 min-h-[460px] max-h-[calc(100vh-330px)]">
          {messages.length === 0 && <div className="text-center py-12"><Bot className="mx-auto text-amber mb-3" size={32} /><h3 className="font-display font-semibold mb-1">What do you want to improve?</h3><p className="text-sm text-muted mb-6">Ask about readiness, eligibility, skill gaps, resumes or interviews.</p><div className="flex flex-wrap gap-2 justify-center max-w-3xl mx-auto">{SUGGESTIONS.map((s) => <button key={s} onClick={() => send(s)} className="suggestion-chip">{s}</button>)}</div></div>}
          {messages.map((m, i) => <Message key={i} message={m} />)}
          {loading && <div className="flex gap-3 items-start"><div className="ai-mini"><Bot size={14} /></div><div className="coach-bubble"><span className="typing"><i></i><i></i><i></i></span><span className="text-xs text-muted ml-2">Coach is analyzing your profile…</span></div></div>}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-border p-4 bg-surface/60"><div className="flex gap-3 items-end"><textarea className="input-field min-h-12 max-h-32 resize-y" rows={1} placeholder="Ask: What is my weakest area right now?" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } }} /><button className="btn-primary h-12 px-4 flex items-center justify-center" onClick={() => send()} disabled={loading || !input.trim()}><Send size={16} /></button></div><p className="text-[11px] text-muted mt-2">Enter to send · Shift+Enter for a new line</p></div>
      </div>
    </Layout>
  );
}

function Message({ message }) {
  const user = message.role === "user";
  return <div className={`flex gap-3 items-start ${user ? "justify-end" : "justify-start"}`}>
    {!user && <div className="ai-mini"><Bot size={14} /></div>}
    <div className={`message-bubble ${user ? "user-bubble" : "coach-bubble"} ${message.error ? "error-bubble" : ""}`}>{message.content}</div>
    {user && <div className="user-mini"><User size={14} /></div>}
  </div>;
}
