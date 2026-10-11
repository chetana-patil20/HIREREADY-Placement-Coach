import React, { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import StatusChip from "../components/StatusChip";
import api from "../services/api";

const ROLE_OPTIONS = ["Python Developer", "AI Engineer", "Data Analyst", "Frontend Developer", "Software Developer"];

export default function SkillGap() {
  const [params] = useSearchParams();
  const [role, setRole] = useState(params.get("role") || "");
  const [gap, setGap] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const load = async (r) => {
    if (!r) return;
    setLoading(true);
    try {
      const res = await api.get("/api/student/skill-gap", { params: { role: r } });
      setGap(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (role) load(role);
    else {
      api.get("/api/student/profile").then((res) => {
        if (res.data.target_role) { setRole(res.data.target_role); load(res.data.target_role); }
      });
    }
  }, []); // eslint-disable-line

  const variant = (status) => status === "Strong" ? "strong" : status === "Needs Improvement" ? "needs improvement" : "missing";

  return (
    <Layout title="Skill gap analysis" subtitle="Compares your actual skills against what each target role requires.">
      <div className="card p-4 mb-5 flex items-end gap-3">
        <div>
          <label className="text-xs text-muted mb-1 block">Target role</label>
          <select className="input-field w-64" value={role} onChange={(e) => { setRole(e.target.value); load(e.target.value); }}>
            <option value="">Select a role</option>
            {ROLE_OPTIONS.map((r) => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {loading && <Loading />}
      {!loading && gap && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-5">
            <div className="card p-4 text-center"><div className="font-display text-2xl font-semibold text-mint">{gap.strong_count}</div><div className="text-xs text-muted">Strong</div></div>
            <div className="card p-4 text-center"><div className="font-display text-2xl font-semibold text-amber">{gap.improve_count}</div><div className="text-xs text-muted">Needs improvement</div></div>
            <div className="card p-4 text-center"><div className="font-display text-2xl font-semibold text-coral">{gap.missing_count}</div><div className="text-xs text-muted">Missing</div></div>
          </div>

          <div className="card p-6 mb-5">
            <h3 className="font-display text-sm font-semibold mb-4">Skill checklist</h3>
            <div className="divide-y divide-border">
              {gap.items.map((item) => (
                <div key={item.skill_name} className="flex items-center justify-between py-2.5">
                  <div>
                    <span className="text-sm">{item.skill_name}</span>
                    <span className="text-xs text-muted ml-2">({item.importance})</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-muted">{item.proficiency}/100</span>
                    <StatusChip label={item.status} variant={variant(item.status)} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="card p-6">
            <h3 className="font-display text-sm font-semibold mb-3">Top skills to learn next</h3>
            {gap.top_skills_to_learn.length === 0 ? (
              <p className="text-sm text-muted">You're covering the required skills well — focus on projects and interviews.</p>
            ) : (
              <ol className="space-y-2 text-sm mb-4">
                {gap.top_skills_to_learn.map((s, i) => <li key={s}>{i + 1}. {s}</li>)}
              </ol>
            )}
            <button className="btn-primary" onClick={() => navigate(`/preparation-plan?role=${encodeURIComponent(role)}`)}>
              Generate a preparation plan for this role
            </button>
          </div>
        </>
      )}
    </Layout>
  );
}
