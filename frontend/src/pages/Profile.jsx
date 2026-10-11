import React, { useEffect, useState } from "react";
import { Plus, Trash2, Save, ExternalLink, Github, Linkedin } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

const TARGET_ROLES = ["Python Developer", "AI Engineer", "Data Analyst", "Frontend Developer", "Software Developer"];

const blankProject = () => ({ title: "", description: "", tech_stack: "", link: "" });
const blankCertification = () => ({ title: "", issuer: "", year: new Date().getFullYear(), credential_url: "" });

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    api.get("/api/student/profile")
      .then((res) => setProfile(res.data))
      .catch((err) => showToast(err.response?.data?.detail || "Could not load profile.", "error"))
      .finally(() => setLoading(false));
  }, []);

  const update = (field, value) => setProfile((p) => ({ ...p, [field]: value }));
  const updateSkill = (idx, field, value) => update("skills", profile.skills.map((s, i) => i === idx ? { ...s, [field]: value } : s));
  const addSkill = () => update("skills", [...profile.skills, { skill_name: "", proficiency: 50 }]);
  const removeSkill = (idx) => update("skills", profile.skills.filter((_, i) => i !== idx));
  const updateListItem = (key, idx, field, value) => update(key, profile[key].map((item, i) => i === idx ? { ...item, [field]: value } : item));
  const addListItem = (key, item) => update(key, [...profile[key], item]);
  const removeListItem = (key, idx) => update(key, profile[key].filter((_, i) => i !== idx));

  const handleSave = async () => {
    const invalidSkill = profile.skills.find((s) => !s.skill_name.trim());
    const invalidProject = profile.projects.find((p) => !p.title.trim());
    const invalidCert = profile.certifications.find((c) => !c.title.trim());
    if (invalidSkill || invalidProject || invalidCert) {
      showToast("Complete or remove empty skill, project, or certification rows before saving.", "error");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        branch: profile.branch || "",
        cgpa: Number(profile.cgpa) || 0,
        percentage_10: Number(profile.percentage_10) || 0,
        percentage_12: Number(profile.percentage_12) || 0,
        backlogs: Number(profile.backlogs) || 0,
        graduation_year: Number(profile.graduation_year) || new Date().getFullYear() + 1,
        target_role: profile.target_role || "",
        available_study_hours_per_day: Number(profile.available_study_hours_per_day) || 2,
        soft_skills: profile.soft_skills || "",
        linkedin_url: profile.linkedin_url || "",
        github_url: profile.github_url || "",
        phone: profile.phone || "",
        skills: profile.skills.map((s) => ({ skill_name: s.skill_name.trim(), proficiency: Math.max(0, Math.min(100, Number(s.proficiency) || 0)) })),
        projects: profile.projects.map((p) => ({ ...p, title: p.title.trim(), link: p.link?.trim() || "" })),
        certifications: profile.certifications.map((c) => ({ ...c, title: c.title.trim(), year: c.year ? Number(c.year) : null, credential_url: c.credential_url?.trim() || "" })),
        internships: profile.internships,
      };
      const res = await api.put("/api/student/profile", payload);
      setProfile(res.data);
      showToast("Profile saved successfully. Readiness and matching scores will update from this data.", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not save profile.", "error");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Layout title="Profile"><Loading /></Layout>;
  if (!profile) return <Layout title="Profile"><div className="card p-6 text-muted">Profile could not be loaded.</div></Layout>;

  return (
    <Layout title="Your profile" subtitle="This is the source data behind your readiness, skill gaps and placement matches.">
      <div className="space-y-5 pb-24">
        <section className="card p-5 md:p-6 reveal">
          <SectionTitle title="Academic details" subtitle="Keep these values accurate because eligibility rules use them." />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Field label="Branch"><input className="input-field" value={profile.branch || ""} onChange={(e) => update("branch", e.target.value)} /></Field>
            <Field label="CGPA"><input className="input-field" type="number" min="0" max="10" step="0.1" value={profile.cgpa ?? ""} onChange={(e) => update("cgpa", e.target.value)} /></Field>
            <Field label="10th percentage"><input className="input-field" type="number" min="0" max="100" step="0.1" value={profile.percentage_10 ?? ""} onChange={(e) => update("percentage_10", e.target.value)} /></Field>
            <Field label="12th percentage"><input className="input-field" type="number" min="0" max="100" step="0.1" value={profile.percentage_12 ?? ""} onChange={(e) => update("percentage_12", e.target.value)} /></Field>
            <Field label="Active backlogs"><input className="input-field" type="number" min="0" value={profile.backlogs ?? ""} onChange={(e) => update("backlogs", e.target.value)} /></Field>
            <Field label="Graduation year"><input className="input-field" type="number" value={profile.graduation_year ?? ""} onChange={(e) => update("graduation_year", e.target.value)} /></Field>
            <Field label="Target role">
              <select className="input-field" value={profile.target_role || ""} onChange={(e) => update("target_role", e.target.value)}>
                <option value="">Select a role</option>
                {TARGET_ROLES.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="Study hours per day"><input className="input-field" type="number" min="0" max="24" step="0.5" value={profile.available_study_hours_per_day ?? ""} onChange={(e) => update("available_study_hours_per_day", e.target.value)} /></Field>
          </div>
        </section>

        <section className="card p-5 md:p-6 reveal">
          <SectionTitle title="Contact & professional links" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Phone"><input className="input-field" value={profile.phone || ""} onChange={(e) => update("phone", e.target.value)} /></Field>
            <Field label="Soft skills" hint="Comma separated"><input className="input-field" value={profile.soft_skills || ""} onChange={(e) => update("soft_skills", e.target.value)} placeholder="Communication, teamwork, leadership" /></Field>
            <Field label="GitHub URL"><div className="relative"><Github className="input-icon" size={16} /><input className="input-field pl-10" value={profile.github_url || ""} onChange={(e) => update("github_url", e.target.value)} placeholder="https://github.com/username" /></div></Field>
            <Field label="LinkedIn URL"><div className="relative"><Linkedin className="input-icon" size={16} /><input className="input-field pl-10" value={profile.linkedin_url || ""} onChange={(e) => update("linkedin_url", e.target.value)} placeholder="https://linkedin.com/in/username" /></div></Field>
          </div>
        </section>

        <section className="card p-5 md:p-6 reveal">
          <SectionHeader title="Technical skills" subtitle="Give each skill a realistic proficiency from 0 to 100." action={<button onClick={addSkill} className="btn-secondary text-xs flex items-center gap-1.5"><Plus size={14} /> Add skill</button>} />
          <div className="space-y-3">
            {profile.skills.map((s, idx) => (
              <div key={idx} className="profile-row-grid">
                <Field label="Skill name"><input className="input-field" placeholder="e.g. Python" value={s.skill_name || ""} onChange={(e) => updateSkill(idx, "skill_name", e.target.value)} /></Field>
                <Field label="Proficiency"><div className="skill-score-wrap"><input className="input-field" type="number" min="0" max="100" value={s.proficiency ?? 0} onChange={(e) => updateSkill(idx, "proficiency", e.target.value)} /><span>/ 100</span></div></Field>
                <button className="delete-button" title="Remove skill" onClick={() => removeSkill(idx)}><Trash2 size={16} /></button>
              </div>
            ))}
            {!profile.skills.length && <EmptyInline text="No technical skills yet. Add the skills you actually know." />}
          </div>
        </section>

        <section className="card p-5 md:p-6 reveal">
          <SectionHeader title="Projects" subtitle="Use clear labels so recruiters and the matching engine can understand your work." action={<button onClick={() => addListItem("projects", blankProject())} className="btn-secondary text-xs flex items-center gap-1.5"><Plus size={14} /> Add project</button>} />
          <div className="space-y-5">
            {profile.projects.map((p, idx) => (
              <div key={idx} className="nested-card">
                <div className="flex items-start justify-between gap-3 mb-4"><div><span className="eyebrow">PROJECT {idx + 1}</span><h3 className="font-display font-semibold mt-1">Project details</h3></div><button className="delete-button" title="Remove project" onClick={() => removeListItem("projects", idx)}><Trash2 size={16} /></button></div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Field label="Project title"><input className="input-field" placeholder="e.g. HireReady - Placement Coach" value={p.title || ""} onChange={(e) => updateListItem("projects", idx, "title", e.target.value)} /></Field>
                  <Field label="Tech stack"><input className="input-field" placeholder="Python, React, FastAPI, SQL" value={p.tech_stack || ""} onChange={(e) => updateListItem("projects", idx, "tech_stack", e.target.value)} /></Field>
                  <Field label="Description"><textarea className="input-field min-h-28 resize-y" placeholder="What did you build, why, and what did it achieve?" value={p.description || ""} onChange={(e) => updateListItem("projects", idx, "description", e.target.value)} /></Field>
                  <Field label="GitHub / project link"><div className="relative"><Github className="input-icon" size={16} /><input className="input-field pl-10" placeholder="https://github.com/..." value={p.link || ""} onChange={(e) => updateListItem("projects", idx, "link", e.target.value)} /></div></Field>
                </div>
                {p.link && <a className="inline-link mt-3" href={p.link.startsWith("http") ? p.link : `https://${p.link}`} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Open project link</a>}
              </div>
            ))}
            {!profile.projects.length && <EmptyInline text="Add at least one real project. Projects directly influence your readiness and role matching." />}
          </div>
        </section>

        <section className="card p-5 md:p-6 reveal">
          <SectionHeader title="Certifications" subtitle="Add the certificate title, issuer, year and a verifiable credential link when available." action={<button onClick={() => addListItem("certifications", blankCertification())} className="btn-secondary text-xs flex items-center gap-1.5"><Plus size={14} /> Add certification</button>} />
          <div className="space-y-4">
            {profile.certifications.map((c, idx) => (
              <div key={idx} className="nested-card">
                <div className="flex items-start justify-between gap-3 mb-4"><div><span className="eyebrow">CERTIFICATION {idx + 1}</span><h3 className="font-display font-semibold mt-1">Credential details</h3></div><button className="delete-button" title="Remove certification" onClick={() => removeListItem("certifications", idx)}><Trash2 size={16} /></button></div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Field label="Certification title"><input className="input-field" placeholder="e.g. Python for Data Science" value={c.title || ""} onChange={(e) => updateListItem("certifications", idx, "title", e.target.value)} /></Field>
                  <Field label="Issuing organization"><input className="input-field" placeholder="e.g. NPTEL, Coursera" value={c.issuer || ""} onChange={(e) => updateListItem("certifications", idx, "issuer", e.target.value)} /></Field>
                  <Field label="Year"><input className="input-field" type="number" min="1990" max="2100" placeholder="2026" value={c.year ?? ""} onChange={(e) => updateListItem("certifications", idx, "year", e.target.value)} /></Field>
                  <Field label="Credential URL"><input className="input-field" placeholder="https://..." value={c.credential_url || ""} onChange={(e) => updateListItem("certifications", idx, "credential_url", e.target.value)} /></Field>
                </div>
                {c.credential_url && <a className="inline-link mt-3" href={c.credential_url.startsWith("http") ? c.credential_url : `https://${c.credential_url}`} target="_blank" rel="noreferrer"><ExternalLink size={14} /> Verify credential</a>}
              </div>
            ))}
            {!profile.certifications.length && <EmptyInline text="No certifications yet. Add certificates that you can genuinely verify." />}
          </div>
        </section>

        <section className="card p-5 md:p-6 reveal">
          <SectionHeader title="Internships" subtitle="Add relevant practical experience so matching can account for it." action={<button onClick={() => addListItem("internships", { company_name: "", role: "", duration_months: 1, description: "" })} className="btn-secondary text-xs flex items-center gap-1.5"><Plus size={14} /> Add internship</button>} />
          <div className="space-y-4">
            {profile.internships.map((i, idx) => (
              <div key={idx} className="nested-card">
                <div className="flex items-start justify-between gap-3 mb-4"><span className="eyebrow">INTERNSHIP {idx + 1}</span><button className="delete-button" title="Remove internship" onClick={() => removeListItem("internships", idx)}><Trash2 size={16} /></button></div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Field label="Company"><input className="input-field" value={i.company_name || ""} onChange={(e) => updateListItem("internships", idx, "company_name", e.target.value)} /></Field>
                  <Field label="Role"><input className="input-field" value={i.role || ""} onChange={(e) => updateListItem("internships", idx, "role", e.target.value)} /></Field>
                  <Field label="Duration (months)"><input className="input-field" type="number" min="1" value={i.duration_months ?? 1} onChange={(e) => updateListItem("internships", idx, "duration_months", e.target.value)} /></Field>
                  <div className="md:col-span-3"><Field label="Description"><textarea className="input-field min-h-24 resize-y" value={i.description || ""} onChange={(e) => updateListItem("internships", idx, "description", e.target.value)} /></Field></div>
                </div>
              </div>
            ))}
            {!profile.internships.length && <EmptyInline text="No internships added." />}
          </div>
        </section>

        <div className="sticky-savebar">
          <div><p className="font-display font-semibold text-sm">Ready to update your placement intelligence?</p><p className="text-xs text-muted">Save once after editing. All derived scores are recalculated from your stored profile.</p></div>
          <button onClick={handleSave} className="btn-primary flex items-center gap-2" disabled={saving}><Save size={15} /> {saving ? "Saving..." : "Save profile"}</button>
        </div>
      </div>
    </Layout>
  );
}

function SectionTitle({ title, subtitle }) { return <div className="mb-5"><h2 className="font-display text-base font-semibold">{title}</h2>{subtitle && <p className="text-xs text-muted mt-1">{subtitle}</p>}</div>; }
function SectionHeader({ title, subtitle, action }) { return <div className="flex items-start justify-between gap-4 mb-5"><SectionTitle title={title} subtitle={subtitle} /><div className="shrink-0">{action}</div></div>; }
function Field({ label, hint, children }) { return <div className="min-w-0"><label className="text-xs font-medium text-text mb-1.5 block">{label}{hint && <span className="text-muted font-normal"> · {hint}</span>}</label>{children}</div>; }
function EmptyInline({ text }) { return <div className="empty-inline">{text}</div>; }
