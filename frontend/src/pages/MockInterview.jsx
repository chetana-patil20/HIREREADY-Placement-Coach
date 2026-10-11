import React, { useState } from "react";
import { Mic, Send, RotateCcw } from "lucide-react";
import Layout from "../components/Layout";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

const MODES = ["HR", "Technical", "Aptitude", "Role-specific"];

export default function MockInterview() {
  const [mode, setMode] = useState("Technical");
  const [role, setRole] = useState("");
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [answer, setAnswer] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [complete, setComplete] = useState(false);
  const [overallScore, setOverallScore] = useState(null);
  const { showToast } = useToast();

  const startSession = async () => {
    setLoading(true);
    setComplete(false);
    setHistory([]);
    setOverallScore(null);
    try {
      const res = await api.post("/api/ai/interview/start", { mode, role: role || undefined });
      setSession(res.data.session_id);
      setQuestion(res.data.question);
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not start interview.", "error");
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async () => {
    if (!answer.trim()) return;
    setLoading(true);
    try {
      const res = await api.post("/api/ai/interview/answer", { session_id: session, question_id: question.id, answer });
      setHistory((prev) => [...prev, { question: question.text, answer, evaluation: res.data.evaluation }]);
      setAnswer("");
      if (res.data.session_complete) {
        setComplete(true);
        setOverallScore(res.data.overall_score);
        setQuestion(null);
      } else {
        setQuestion(res.data.next_question);
      }
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not submit answer.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Mock interview" subtitle="Practice HR, technical, aptitude, or role-specific interviews with instant feedback.">
      {!session && (
        <div className="card p-6 max-w-lg">
          <h2 className="font-display text-sm font-semibold mb-4">Start a session</h2>
          <div className="space-y-4">
            <div>
              <label className="text-xs text-muted mb-1 block">Mode</label>
              <div className="grid grid-cols-2 gap-2">
                {MODES.map((m) => (
                  <button key={m} onClick={() => setMode(m)} className={`px-3 py-2 rounded-lg text-sm border transition-colors ${mode === m ? "border-amber text-amber bg-amber/10" : "border-border text-muted"}`}>
                    {m}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-xs text-muted mb-1 block">Target role (optional — defaults to your profile)</label>
              <input className="input-field" value={role} onChange={(e) => setRole(e.target.value)} placeholder="e.g. AI Engineer" />
            </div>
            <button className="btn-primary flex items-center gap-2" onClick={startSession} disabled={loading}>
              <Mic size={15} /> {loading ? "Starting..." : "Start mock interview"}
            </button>
          </div>
        </div>
      )}

      {session && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 space-y-4">
            {question && (
              <div className="card p-6">
                <div className="text-xs text-muted mb-2">{mode} · Question {history.length + 1} of 5</div>
                <p className="text-sm mb-4">{question.text}</p>
                <textarea className="input-field" rows={4} placeholder="Type your answer..." value={answer} onChange={(e) => setAnswer(e.target.value)} />
                <button className="btn-primary mt-3 flex items-center gap-2" onClick={submitAnswer} disabled={loading || !answer.trim()}>
                  <Send size={14} /> {loading ? "Evaluating..." : "Submit answer"}
                </button>
              </div>
            )}

            {complete && (
              <div className="card p-6 text-center">
                <div className="font-display text-3xl font-semibold text-amber mb-1">{overallScore}%</div>
                <p className="text-sm text-muted mb-4">Session complete.</p>
                <button className="btn-secondary flex items-center gap-2 mx-auto" onClick={() => { setSession(null); setHistory([]); }}>
                  <RotateCcw size={14} /> Start another session
                </button>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <h3 className="font-display text-sm font-semibold">Feedback so far</h3>
            {history.length === 0 && <p className="text-sm text-muted">Answer a question to see feedback here.</p>}
            {history.slice().reverse().map((h, i) => (
              <div key={i} className="card p-4 text-sm">
                <p className="text-muted text-xs mb-2">{h.question}</p>
                <div className="flex items-center justify-between mb-2">
                  <span className="font-display font-semibold text-amber">{h.evaluation.score}/100</span>
                </div>
                <p className="text-mint text-xs mb-1">✓ {h.evaluation.strengths}</p>
                <p className="text-coral text-xs mb-1">⚠ {h.evaluation.weaknesses}</p>
                <p className="text-muted text-xs mt-2 italic">Tip: {h.evaluation.improved_answer}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </Layout>
  );
}
