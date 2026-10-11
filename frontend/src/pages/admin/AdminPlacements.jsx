import React, { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import Layout from "../../components/Layout";
import Loading from "../../components/Loading";
import api from "../../services/api";
import { useToast } from "../../context/ToastContext";

const EMPTY_FORM = {
  company_name: "", company_logo_emoji: "🏢", title: "", ctc_lpa: "", location: "", work_mode: "On-site",
  min_cgpa: "", min_percentage_10: "", min_percentage_12: "", max_backlogs: "0",
  eligible_graduation_years: "", eligible_branches: "", required_skills: "", preferred_skills: "",
  min_experience_months: "0", application_deadline: "", drive_date: "", description: "",
};

export default function AdminPlacements() {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const { showToast } = useToast();

  const load = () => api.get("/api/placements").then((res) => { setRoles(res.data); setLoading(false); });

  useEffect(() => { load(); }, []);

  const handleChange = (field, value) => setForm({ ...form, [field]: value });

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        ctc_lpa: Number(form.ctc_lpa || 0),
        min_cgpa: Number(form.min_cgpa || 0),
        min_percentage_10: Number(form.min_percentage_10 || 0),
        min_percentage_12: Number(form.min_percentage_12 || 0),
        max_backlogs: Number(form.max_backlogs || 0),
        min_experience_months: Number(form.min_experience_months || 0),
        application_deadline: form.application_deadline || null,
        drive_date: form.drive_date || null,
      };
      await api.post("/api/admin/placements", payload);
      showToast("Placement drive added.", "success");
      setForm(EMPTY_FORM);
      setShowForm(false);
      load();
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not add placement.", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const remove = async (id) => {
    try {
      await api.delete(`/api/admin/placements/${id}`);
      showToast("Deleted.", "success");
      load();
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not delete.", "error");
    }
  };

  return (
    <Layout title="Manage placements" subtitle="Add companies, job roles, and eligibility rules.">
      <button className="btn-primary flex items-center gap-2 mb-5" onClick={() => setShowForm(!showForm)}>
        <Plus size={15} /> {showForm ? "Close form" : "Add placement drive"}
      </button>

      {showForm && (
        <form onSubmit={submit} className="card p-6 mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          <Input label="Company name" value={form.company_name} onChange={(v) => handleChange("company_name", v)} required />
          <Input label="Logo emoji" value={form.company_logo_emoji} onChange={(v) => handleChange("company_logo_emoji", v)} />
          <Input label="Job title" value={form.title} onChange={(v) => handleChange("title", v)} required />
          <Input label="CTC (LPA)" type="number" value={form.ctc_lpa} onChange={(v) => handleChange("ctc_lpa", v)} required />
          <Input label="Location" value={form.location} onChange={(v) => handleChange("location", v)} />
          <div>
            <label className="text-xs text-muted mb-1 block">Work mode</label>
            <select className="input-field" value={form.work_mode} onChange={(e) => handleChange("work_mode", e.target.value)}>
              <option>On-site</option><option>Remote</option><option>Hybrid</option>
            </select>
          </div>
          <Input label="Min CGPA" type="number" step="0.1" value={form.min_cgpa} onChange={(v) => handleChange("min_cgpa", v)} required />
          <Input label="Max backlogs" type="number" value={form.max_backlogs} onChange={(v) => handleChange("max_backlogs", v)} />
          <Input label="Min 10th %" type="number" value={form.min_percentage_10} onChange={(v) => handleChange("min_percentage_10", v)} />
          <Input label="Min 12th %" type="number" value={form.min_percentage_12} onChange={(v) => handleChange("min_percentage_12", v)} />
          <Input label="Min experience (months)" type="number" value={form.min_experience_months} onChange={(v) => handleChange("min_experience_months", v)} />
          <Input label="Eligible grad years (csv)" value={form.eligible_graduation_years} onChange={(v) => handleChange("eligible_graduation_years", v)} placeholder="2026,2027" />
          <Input label="Eligible branches (csv, blank=all)" value={form.eligible_branches} onChange={(v) => handleChange("eligible_branches", v)} />
          <Input label="Required skills (csv)" value={form.required_skills} onChange={(v) => handleChange("required_skills", v)} className="col-span-2" />
          <Input label="Preferred skills (csv)" value={form.preferred_skills} onChange={(v) => handleChange("preferred_skills", v)} className="col-span-2" />
          <Input label="Application deadline" type="date" value={form.application_deadline} onChange={(v) => handleChange("application_deadline", v)} />
          <Input label="Drive date" type="date" value={form.drive_date} onChange={(v) => handleChange("drive_date", v)} />
          <div className="col-span-2 md:col-span-4">
            <label className="text-xs text-muted mb-1 block">Description</label>
            <textarea className="input-field" rows={2} value={form.description} onChange={(e) => handleChange("description", e.target.value)} />
          </div>
          <div className="col-span-2 md:col-span-4">
            <button className="btn-primary" type="submit" disabled={submitting}>{submitting ? "Saving..." : "Save placement drive"}</button>
          </div>
        </form>
      )}

      {loading ? <Loading /> : (
        <div className="space-y-3">
          {roles.map((r) => (
            <div key={r.id} className="card p-4 flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">{r.company_logo_emoji} {r.title} — {r.company_name}</div>
                <div className="text-xs text-muted mt-0.5">{r.ctc_lpa} LPA · {r.location} · Min CGPA {r.min_cgpa} · Deadline {r.application_deadline || "—"}</div>
              </div>
              <button onClick={() => remove(r.id)} className="text-xs text-coral">Delete</button>
            </div>
          ))}
          {roles.length === 0 && <p className="text-sm text-muted">No placement drives yet.</p>}
        </div>
      )}
    </Layout>
  );
}

function Input({ label, className = "", ...props }) {
  return (
    <div className={className}>
      <label className="text-xs text-muted mb-1 block">{label}</label>
      <input className="input-field" {...props} onChange={(e) => props.onChange(e.target.value)} />
    </div>
  );
}
