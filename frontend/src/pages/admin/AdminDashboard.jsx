import React, { useEffect, useState } from "react";
import { Users, CheckCircle2, TrendingUp, Briefcase } from "lucide-react";
import Layout from "../../components/Layout";
import Loading from "../../components/Loading";
import api from "../../services/api";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get("/api/admin/dashboard"), api.get("/api/admin/students")]).then(([d, s]) => {
      setData(d.data);
      setStudents(s.data);
      setLoading(false);
    });
  }, []);

  if (loading) return <Layout title="Admin dashboard"><Loading /></Layout>;

  const stats = [
    { label: "Total students", value: data.total_students, icon: Users },
    { label: "Placement eligible", value: data.placement_eligible, icon: CheckCircle2 },
    { label: "Placement ready (60%+)", value: data.placement_ready, icon: TrendingUp },
    { label: "Applications", value: data.total_applications, icon: Briefcase },
  ];

  return (
    <Layout title="Admin dashboard" subtitle={`${data.total_companies} companies · ${data.total_job_roles} active job roles`}>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
        {stats.map((s) => (
          <div key={s.label} className="card p-5">
            <s.icon size={18} className="text-amber mb-2" />
            <div className="font-display text-2xl font-semibold">{s.value}</div>
            <div className="text-xs text-muted mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-5">
        <div className="card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Top skills across students</h3>
          <div className="space-y-2">
            {data.top_skills.map(([skill, count]) => (
              <BarRow key={skill} label={skill} value={count} max={data.top_skills[0]?.[1] || 1} color="bg-mint" />
            ))}
            {data.top_skills.length === 0 && <p className="text-sm text-muted">No skill data yet.</p>}
          </div>
        </div>
        <div className="card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Top skill gaps</h3>
          <div className="space-y-2">
            {data.top_skill_gaps.map(([skill, count]) => (
              <BarRow key={skill} label={skill} value={count} max={data.top_skill_gaps[0]?.[1] || 1} color="bg-coral" />
            ))}
            {data.top_skill_gaps.length === 0 && <p className="text-sm text-muted">No gap data yet.</p>}
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-display text-sm font-semibold mb-4">Student overview</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-muted border-b border-border">
              <tr>
                <th className="text-left py-2">Name</th>
                <th className="text-left py-2">Target role</th>
                <th className="text-left py-2">CGPA</th>
                <th className="text-left py-2">Readiness</th>
                <th className="text-left py-2">Eligible for</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {students.map((s) => (
                <tr key={s.id}>
                  <td className="py-2.5">{s.full_name}</td>
                  <td className="py-2.5 text-muted">{s.target_role || "—"}</td>
                  <td className="py-2.5">{s.cgpa}</td>
                  <td className="py-2.5">{s.readiness}%</td>
                  <td className="py-2.5">{s.eligible_count} role(s)</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}

function BarRow({ label, value, max, color }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="w-28 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-surfacealt overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${(value / max) * 100}%` }} />
      </div>
      <span className="w-6 text-right text-muted text-xs">{value}</span>
    </div>
  );
}
