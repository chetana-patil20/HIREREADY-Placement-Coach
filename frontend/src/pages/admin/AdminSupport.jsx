import React, { useEffect, useState } from "react";
import Layout from "../../components/Layout";
import Loading from "../../components/Loading";
import StatusChip from "../../components/StatusChip";
import api from "../../services/api";
import { useToast } from "../../context/ToastContext";

const STATUSES = ["Pending", "In Progress", "Resolved"];

export default function AdminSupport() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const { showToast } = useToast();

  const load = () => api.get("/api/admin/support-tickets").then((res) => { setTickets(res.data); setLoading(false); });

  useEffect(() => { load(); }, []);

  const updateStatus = async (id, status) => {
    try {
      await api.put(`/api/admin/support-tickets/${id}`, { status });
      setTickets((prev) => prev.map((t) => (t.id === id ? { ...t, status } : t)));
      showToast("Ticket updated.", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not update ticket.", "error");
    }
  };

  if (loading) return <Layout title="Support tickets"><Loading /></Layout>;

  return (
    <Layout title="Support tickets" subtitle="Student-submitted IT, classroom, infrastructure, and placement issues.">
      <div className="space-y-3">
        {tickets.map((t) => (
          <div key={t.id} className="card p-4 flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium">{t.subject}</span>
                <StatusChip label={t.category} variant="neutral" />
              </div>
              <p className="text-xs text-muted">{t.student_name} · {t.description || "No description"}</p>
            </div>
            <select className="input-field w-40 shrink-0" value={t.status} onChange={(e) => updateStatus(t.id, e.target.value)}>
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        ))}
        {tickets.length === 0 && <p className="text-sm text-muted">No support tickets yet.</p>}
      </div>
    </Layout>
  );
}
