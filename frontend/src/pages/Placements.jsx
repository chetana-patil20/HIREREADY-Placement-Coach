import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { MapPin, IndianRupee, Clock } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import StatusChip from "../components/StatusChip";
import api from "../services/api";

export default function Placements() {
  const [roles, setRoles] = useState([]);
  const [matches, setMatches] = useState({});
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ role: "", location: "", min_ctc: "" });
  const [sortBy, setSortBy] = useState("match");

  const load = async () => {
    setLoading(true);
    const params = {};
    if (filters.role) params.role = filters.role;
    if (filters.location) params.location = filters.location;
    if (filters.min_ctc) params.min_ctc = filters.min_ctc;
    const [rolesRes, matchesRes] = await Promise.all([
      api.get("/api/placements", { params }),
      api.get("/api/student/matches"),
    ]);
    const matchMap = {};
    matchesRes.data.forEach((m) => (matchMap[m.job_role_id] = m));
    setRoles(rolesRes.data);
    setMatches(matchMap);
    setLoading(false);
  };

  useEffect(() => { load(); }, []); // eslint-disable-line

  const sorted = [...roles].sort((a, b) => {
    if (sortBy === "match") return (matches[b.id]?.overall_match || 0) - (matches[a.id]?.overall_match || 0);
    if (sortBy === "ctc") return b.ctc_lpa - a.ctc_lpa;
    if (sortBy === "deadline") return new Date(a.application_deadline || "9999-12-31") - new Date(b.application_deadline || "9999-12-31");
    return 0;
  });

  return (
    <Layout title="Placement opportunities" subtitle="Deterministic eligibility and match scoring for every listed drive.">
      <div className="card p-4 mb-5 flex flex-wrap items-end gap-3">
        <div>
          <label className="text-xs text-muted mb-1 block">Role</label>
          <input className="input-field w-44" value={filters.role} onChange={(e) => setFilters({ ...filters, role: e.target.value })} placeholder="e.g. Developer" />
        </div>
        <div>
          <label className="text-xs text-muted mb-1 block">Location</label>
          <input className="input-field w-40" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} placeholder="e.g. Bengaluru" />
        </div>
        <div>
          <label className="text-xs text-muted mb-1 block">Min CTC (LPA)</label>
          <input className="input-field w-32" type="number" value={filters.min_ctc} onChange={(e) => setFilters({ ...filters, min_ctc: e.target.value })} />
        </div>
        <button className="btn-primary" onClick={load}>Apply filters</button>
        <div className="ml-auto">
          <label className="text-xs text-muted mb-1 block">Sort by</label>
          <select className="input-field" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="match">Best match</option>
            <option value="ctc">Highest CTC</option>
            <option value="deadline">Deadline soonest</option>
          </select>
        </div>
      </div>

      {loading ? <Loading /> : sorted.length === 0 ? (
        <EmptyState title="No placement opportunities found" description="Try adjusting your filters." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sorted.map((r) => {
            const m = matches[r.id];
            return (
              <Link to={`/placements/${r.id}`} key={r.id} className="card p-5 hover:border-amber/50 transition-colors block">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <span className="text-2xl">{r.company_logo_emoji}</span>
                    <div>
                      <div className="font-display text-sm font-semibold">{r.title}</div>
                      <div className="text-xs text-muted">{r.company_name}</div>
                    </div>
                  </div>
                  {m && <span className="font-display text-lg font-semibold text-amber">{m.overall_match}%</span>}
                </div>
                <div className="flex flex-wrap gap-3 text-xs text-muted mb-3">
                  <span className="flex items-center gap-1"><IndianRupee size={12} /> {r.ctc_lpa} LPA</span>
                  <span className="flex items-center gap-1"><MapPin size={12} /> {r.location} · {r.work_mode}</span>
                  {r.application_deadline && <span className="flex items-center gap-1"><Clock size={12} /> Closes {r.application_deadline}</span>}
                </div>
                {m && <StatusChip label={m.eligible ? "Eligible" : "Not eligible"} variant={m.eligible ? "eligible" : "not-eligible"} />}
              </Link>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
