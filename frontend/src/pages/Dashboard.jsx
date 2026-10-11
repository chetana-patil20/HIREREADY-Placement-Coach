import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Briefcase, Target, CalendarClock, FileText, ArrowRight, CheckCircle2, Circle } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import ProgressBar from "../components/ProgressBar";
import StatusChip from "../components/StatusChip";
import api from "../services/api";

const READINESS_ROWS = [
  { key: "academic", label: "Academic" },
  { key: "technical_skills", label: "Technical Skills" },
  { key: "projects", label: "Projects" },
  { key: "resume", label: "Resume" },
  { key: "aptitude", label: "Aptitude" },
  { key: "interview", label: "Interview" },
];

function ringColor(v) {
  if (v >= 70) return "#3ECF8E";
  if (v >= 40) return "#E8A33D";
  return "#F2555A";
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/student/dashboard").then((res) => setData(res.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout title="Dashboard"><Loading /></Layout>;
  if (!data) return <Layout title="Dashboard"><p className="text-muted">Couldn't load your dashboard.</p></Layout>;

  const overall = data.readiness.overall;
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (overall / 100) * circumference;

  return (
    <Layout title={`Welcome back, ${data.full_name?.split(" ")[0] || "there"}`} subtitle={data.target_role ? `Target role: ${data.target_role}` : "Set a target role in your profile to unlock skill-gap analysis"}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Readiness hero */}
        <div className="card p-6 lg:col-span-1 flex flex-col items-center justify-center text-center">
          <div className="relative w-36 h-36">
            <svg width="144" height="144" viewBox="0 0 144 144" className="-rotate-90">
              <circle cx="72" cy="72" r="54" fill="none" stroke="#2A3348" strokeWidth="12" />
              <circle
                cx="72" cy="72" r="54" fill="none" stroke={ringColor(overall)} strokeWidth="12"
                strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="font-display text-3xl font-semibold">{overall}%</span>
              <span className="text-[11px] text-muted">readiness</span>
            </div>
          </div>
          <p className="text-sm text-muted mt-4">Placement Readiness Score</p>
          <p className="text-xs text-muted mt-1">Weakest area: <span className="text-coral">{data.readiness.weakest_area}</span></p>
        </div>

        {/* Breakdown */}
        <div className="card p-6 lg:col-span-2">
          <h2 className="font-display text-sm font-semibold mb-4">Readiness breakdown</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-4">
            {READINESS_ROWS.map((r) => (
              <ProgressBar key={r.key} label={r.label} value={data.readiness[r.key]} colorClass={data.readiness[r.key] < 40 ? "bg-coral" : data.readiness[r.key] < 70 ? "bg-amber" : "bg-mint"} />
            ))}
          </div>
        </div>
      </div>

      <div className="card p-6 mt-5">
        <h2 className="font-display text-sm font-semibold mb-2">Your next steps</h2>
        <p className="text-xs text-muted mb-4">{data.readiness.score_meaning}</p>
        <ol className="space-y-2 list-decimal list-inside text-sm">
          {(data.readiness.next_actions || []).map((action, i) => <li key={i}>{action}</li>)}
        </ol>
        <p className="text-[11px] text-muted mt-4">Readiness weights: academics {Math.round(data.readiness.weights.academic * 100)}% · skills {Math.round(data.readiness.weights.technical_skills * 100)}% · projects {Math.round(data.readiness.weights.projects * 100)}% · resume {Math.round(data.readiness.weights.resume * 100)}% · aptitude {Math.round(data.readiness.weights.aptitude * 100)}% · interviews {Math.round(data.readiness.weights.interview * 100)}%.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-5">
        {/* Top matches */}
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-sm font-semibold">Top matching opportunities</h2>
            <Link to="/placements" className="text-xs text-amber flex items-center gap-1">View all <ArrowRight size={13} /></Link>
          </div>
          <div className="space-y-3">
            {data.top_matches.length === 0 && <p className="text-sm text-muted">No placement opportunities available yet.</p>}
            {data.top_matches.map((m) => (
              <Link
                to={`/placements/${m.job_role_id}`}
                key={m.job_role_id}
                className="flex items-center justify-between px-4 py-3 rounded-lg bg-surfacealt hover:bg-surfacealt/70 transition-colors"
              >
                <div>
                  <div className="text-sm font-medium">{m.role_title} — {m.company_name}</div>
                  <div className="text-xs text-muted mt-0.5">{m.matched_skills.length} matched skills</div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusChip label={m.eligible ? "Eligible" : "Not eligible"} variant={m.eligible ? "eligible" : "not-eligible"} />
                  <span className="font-display text-sm font-semibold w-12 text-right">{m.overall_match}%</span>
                </div>
              </Link>
            ))}
          </div>
        </div>

        {/* Today's tasks */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-display text-sm font-semibold">Today's tasks</h2>
            <Link to="/preparation-plan" className="text-xs text-amber flex items-center gap-1">Plan <ArrowRight size={13} /></Link>
          </div>
          {data.today_tasks.length === 0 ? (
            <p className="text-sm text-muted">No plan yet — generate one from Preparation Plan.</p>
          ) : (
            <div className="space-y-2.5">
              {data.today_tasks.map((t) => (
                <div key={t.id} className="flex items-center gap-2.5 text-sm">
                  {t.completed ? <CheckCircle2 size={16} className="text-mint shrink-0" /> : <Circle size={16} className="text-muted shrink-0" />}
                  <span className={t.completed ? "line-through text-muted" : ""}>{t.title}</span>
                </div>
              ))}
              <p className="text-xs text-muted pt-1">{data.pending_task_count} task(s) pending overall</p>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-5">
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3 text-sm font-semibold font-display"><CalendarClock size={16} className="text-amber" /> Upcoming deadlines</div>
          {data.upcoming_deadlines.length === 0 ? <p className="text-sm text-muted">Nothing in the next few weeks.</p> :
            <ul className="space-y-2 text-sm">
              {data.upcoming_deadlines.map((d) => (
                <li key={d.id} className="flex justify-between"><span>{d.company_name} — {d.role}</span><span className="text-muted">{d.application_deadline}</span></li>
              ))}
            </ul>}
        </div>
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3 text-sm font-semibold font-display"><Briefcase size={16} className="text-amber" /> Upcoming drives</div>
          {data.upcoming_drives.length === 0 ? <p className="text-sm text-muted">No drives scheduled yet.</p> :
            <ul className="space-y-2 text-sm">
              {data.upcoming_drives.map((d) => (
                <li key={d.id} className="flex justify-between"><span>{d.company_name} — {d.role}</span><span className="text-muted">{d.drive_date}</span></li>
              ))}
            </ul>}
        </div>
        <div className="card p-6">
          <div className="flex items-center gap-2 mb-3 text-sm font-semibold font-display"><FileText size={16} className="text-amber" /> AI recommendations</div>
          <ul className="space-y-2 text-sm text-muted">
            {data.recommendations.slice(0, 4).map((r, i) => <li key={i}>• {r}</li>)}
          </ul>
        </div>
      </div>

      {data.skill_gap && (
        <div className="card p-6 mt-5">
          <div className="flex items-center gap-2 mb-3 text-sm font-semibold font-display"><Target size={16} className="text-amber" /> Skill gap for {data.skill_gap.role_name}</div>
          <div className="flex flex-wrap gap-2">
            {data.skill_gap.top_skills_to_learn.map((s) => <StatusChip key={s} label={s} variant="missing" />)}
            {data.skill_gap.top_skills_to_learn.length === 0 && <p className="text-sm text-muted">You're covering the required skills well.</p>}
          </div>
        </div>
      )}
    </Layout>
  );
}
