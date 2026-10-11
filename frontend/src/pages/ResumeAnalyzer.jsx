import React, { useEffect, useState } from "react";
import { FileText, CheckCircle2 } from "lucide-react";
import Layout from "../components/Layout";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

export default function ResumeAnalyzer() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    api.get("/api/student/profile").then((res) => setText(res.data.resume_text || ""));
  }, []);

  const analyze = async () => {
    if (!text.trim()) { showToast("Paste your resume text first.", "error"); return; }
    setLoading(true);
    try {
      const res = await api.post("/api/ai/resume-analysis", { resume_text: text });
      setResult(res.data);
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not analyze resume.", "error");
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = result ? (result.score >= 70 ? "text-mint" : result.score >= 40 ? "text-amber" : "text-coral") : "";

  return (
    <Layout title="Resume analyzer" subtitle="Paste your resume text to get a completeness score and specific, non-invented suggestions.">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3 text-sm font-semibold font-display"><FileText size={15} className="text-amber" /> Resume text</div>
          <textarea className="input-field" rows={16} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste your resume content here..." />
          <button className="btn-primary mt-3" onClick={analyze} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze resume"}
          </button>
        </div>

        <div className="space-y-4">
          {!result ? (
            <div className="card p-6 text-sm text-muted">Your resume score, flagged issues, and suggestions will appear here.</div>
          ) : (
            <>
              <div className="card p-6 text-center">
                <div className={`font-display text-4xl font-semibold ${scoreColor}`}>{result.score}/100</div>
                <p className="text-xs text-muted mt-1">Resume completeness score</p>
                <div className="flex justify-center gap-4 mt-3 text-xs text-muted">
                  <span>{result.word_count} words</span>
                  <span>{result.has_github ? "✓ GitHub linked" : "✗ No GitHub link"}</span>
                  <span>{result.has_linkedin ? "✓ LinkedIn linked" : "✗ No LinkedIn link"}</span>
                </div>
              </div>

              {result.problems.length > 0 && (
                <div className="card p-6">
                  <h3 className="font-display text-sm font-semibold mb-3">Problems found</h3>
                  <ul className="space-y-2 text-sm text-coral">
                    {result.problems.map((p, i) => <li key={i}>• {p}</li>)}
                  </ul>
                </div>
              )}

              <div className="card p-6">
                <h3 className="font-display text-sm font-semibold mb-3">Suggestions</h3>
                <ul className="space-y-2 text-sm">
                  {result.suggestions.map((s, i) => (
                    <li key={i} className="flex items-start gap-2"><CheckCircle2 size={14} className="text-mint shrink-0 mt-0.5" /> {s}</li>
                  ))}
                </ul>
              </div>
            </>
          )}
        </div>
      </div>
    </Layout>
  );
}
