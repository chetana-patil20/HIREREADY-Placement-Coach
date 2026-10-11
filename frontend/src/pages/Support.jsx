import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import StatusChip from "../components/StatusChip";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

const CATEGORIES = ["IT", "classroom", "infrastructure", "placement", "other"];

export default function Support() {
  const [tickets, setTickets] = useState([]);
  const [form, setForm] = useState({ category: "IT", subject: "", description: "" });
  const [submitting, setSubmitting] = useState(false);
  const { showToast } = useToast();

  const load = () => api.get("/api/student/support-tickets").then((res) => setTickets(res.data));

  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.subject.trim()) return;
    setSubmitting(true);
    try {
      await api.post("/api/student/support-tickets", form);
      setForm({ category: "IT", subject: "", description: "" });
      showToast("Support ticket submitted.", "success");
      load();
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not submit ticket.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout title="Student support" subtitle="Report an issue — IT, classroom, infrastructure, placement, or other.">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <form onSubmit={submit} className="card p-6 space-y-4 h-fit">
          <h2 className="font-display text-sm font-semibold">New ticket</h2>
          <div>
            <label className="text-xs text-muted mb-1 block">Category</label>
            <select className="input-field" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-muted mb-1 block">Subject</label>
            <input className="input-field" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} required />
          </div>
          <div>
            <label className="text-xs text-muted mb-1 block">Description</label>
            <textarea className="input-field" rows={4} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <button className="btn-primary" type="submit" disabled={submitting}>{submitting ? "Submitting..." : "Submit ticket"}</button>
        </form>

        <div>
          <h2 className="font-display text-sm font-semibold mb-4">Your tickets</h2>
          <div className="space-y-3">
            {tickets.map((t) => (
              <div key={t.id} className="card p-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium">{t.subject}</span>
                  <StatusChip label={t.status} variant={t.status.toLowerCase()} />
                </div>
                <p className="text-xs text-muted">{t.category} · {new Date(t.created_at).toLocaleDateString()}</p>
              </div>
            ))}
            {tickets.length === 0 && <p className="text-sm text-muted">No tickets submitted yet.</p>}
          </div>
        </div>
      </div>
    </Layout>
  );
}
