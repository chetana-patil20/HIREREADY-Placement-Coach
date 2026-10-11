import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { CheckCircle2, XCircle, MapPin, IndianRupee, Clock, Calendar } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import StatusChip from "../components/StatusChip";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

export default function PlacementDetail() {
  const { id } = useParams();
  const [role, setRole] = useState(null);
  const [match, setMatch] = useState(null);
  const [applying, setApplying] = useState(false);
  const { showToast } = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      api.get(`/api/placements/${id}`),
      api.get(`/api/student/matches/${id}`),
    ]).then(([roleRes, matchRes]) => {
      setRole(roleRes.data);
      setMatch(matchRes.data);
    });
  }, [id]);

  const handleApply = async () => {
    setApplying(true);
    try {
      const res = await api.post(`/api/student/apply/${id}`);
      showToast(res.data.message, "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not apply.", "error");
    } finally {
      setApplying(false);
    }
  };

  if (!role || !match) return <Layout title="Placement details"><Loading /></Layout>;

  return (
    <Layout title={`${role.title} at ${role.company_name}`} subtitle={role.description}>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="card p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <StatusChip label={match.eligible ? "Eligible" : "Not eligible"} variant={match.eligible ? "eligible" : "not-eligible"} />
            <span className="font-display text-2xl font-semibold text-amber">{match.overall_match}% match</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm mb-6">
            <Detail icon={IndianRupee} label="CTC" value={`${role.ctc_lpa} LPA`} />
            <Detail icon={MapPin} label="Location" value={`${role.location} · ${role.work_mode}`} />
            <Detail icon={Clock} label="Deadline" value={role.application_deadline || "—"} />
            <Detail icon={Calendar} label="Drive date" value={role.drive_date || "—"} />
          </div>

          <h3 className="font-display text-sm font-semibold mb-2">Why this match score</h3>
          <p className="text-xs text-muted mb-3">The estimate weights skill fit at 55%, academics at 25%, and relevant projects at 20%. It measures profile fit, not your probability of being hired. The eligibility checklist below is a separate pass/fail check against the drive rules.</p>
          <div className="space-y-1.5 text-sm mb-5">
            <ScoreRow label="Skill match" value={match.skill_match} />
            <ScoreRow label="Academic match" value={match.academic_match} />
            <ScoreRow label="Project relevance" value={match.project_relevance} />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-5">
            <div>
              <h4 className="text-xs text-muted mb-2">✓ Matched skills</h4>
              <div className="flex flex-wrap gap-1.5">
                {match.matched_skills.length ? match.matched_skills.map((s) => <StatusChip key={s} label={s} variant="strong" />) : <span className="text-xs text-muted">None yet</span>}
              </div>
            </div>
            <div>
              <h4 className="text-xs text-muted mb-2">⚠ Missing skills</h4>
              <div className="flex flex-wrap gap-1.5">
                {[...match.missing_required_skills, ...match.missing_preferred_skills].length
                  ? [...match.missing_required_skills, ...match.missing_preferred_skills].map((s) => <StatusChip key={s} label={s} variant="missing" />)
                  : <span className="text-xs text-muted">None — full coverage</span>}
              </div>
            </div>
          </div>

          <div className="bg-surfacealt rounded-lg p-4 text-sm mb-5">
            <span className="text-amber font-medium">Recommended action: </span>{match.recommended_action}
          </div>

          {!match.eligible && (
            <div className="border border-coral/40 bg-coral/10 rounded-lg p-4 text-sm mb-5">
              <div className="flex items-center gap-2 text-coral font-medium mb-2"><XCircle size={15} /> Why you're not eligible</div>
              <ul className="space-y-1 text-muted">
                {match.eligibility_reasons.map((r, i) => <li key={i}>• {r}</li>)}
              </ul>
            </div>
          )}

          <div className="flex gap-3">
            <button className="btn-primary" disabled={!match.eligible || applying} onClick={handleApply}>
              {applying ? "Submitting..." : "Apply / Registration"}
            </button>
            <button className="btn-secondary" onClick={() => navigate(`/skill-gap?role=${encodeURIComponent(role.title)}`)}>
              Prepare for this role
            </button>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-display text-sm font-semibold mb-3">Eligibility criteria</h3>
          <ul className="text-sm space-y-2 text-muted">
            <li>Min CGPA: <span className="text-text">{role.min_cgpa}</span></li>
            <li>Max backlogs: <span className="text-text">{role.max_backlogs}</span></li>
            <li>Graduation years: <span className="text-text">{role.eligible_graduation_years || "Any"}</span></li>
            <li>Required skills: <span className="text-text">{role.required_skills || "—"}</span></li>
            <li>Preferred skills: <span className="text-text">{role.preferred_skills || "—"}</span></li>
            {role.min_experience_months > 0 && <li>Min experience: <span className="text-text">{role.min_experience_months} months</span></li>}
          </ul>
        </div>
      </div>
    </Layout>
  );
}

function Detail({ icon: Icon, label, value }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-muted text-xs mb-1"><Icon size={12} /> {label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}

function ScoreRow({ label, value }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 text-muted">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-surfacealt overflow-hidden">
        <div className="h-full bg-amber rounded-full" style={{ width: `${value}%` }} />
      </div>
      <span className="w-10 text-right">{value}%</span>
    </div>
  );
}
