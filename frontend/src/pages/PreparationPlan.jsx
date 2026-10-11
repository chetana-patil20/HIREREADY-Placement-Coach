import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CheckCircle2, Circle, Sparkles } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import api from "../services/api";
import { useToast } from "../context/ToastContext";

export default function PreparationPlan() {
  const [params] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const { showToast } = useToast();

  const load = async () => {
    setLoading(true);
    const res = await api.get("/api/student/preparation-plan");
    setTasks(res.data);
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const generate = async () => {
    setGenerating(true);
    try {
      const role = params.get("role") || undefined;
      const res = await api.post("/api/student/preparation-plan/generate", null, { params: role ? { role } : {} });
      setTasks(res.data);
      showToast("Preparation plan generated.", "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not generate plan.", "error");
    } finally {
      setGenerating(false);
    }
  };

  const toggleTask = async (id) => {
    const res = await api.post(`/api/student/preparation-task/${id}/complete`);
    setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, completed: res.data.completed } : t)));
  };

  const weeks = [1, 2, 3, 4];
  const completed = tasks.filter((t) => t.completed).length;

  return (
    <Layout title="Preparation plan" subtitle="A 4-week, trackable plan built from your actual skill gaps and weakest readiness areas.">
      <div className="flex items-center justify-between mb-5">
        <div className="text-sm text-muted">{tasks.length > 0 ? `${completed} of ${tasks.length} tasks completed` : "No plan generated yet"}</div>
        <button className="btn-primary flex items-center gap-2" onClick={generate} disabled={generating}>
          <Sparkles size={15} /> {generating ? "Generating..." : tasks.length ? "Regenerate plan" : "Generate plan"}
        </button>
      </div>

      {loading ? <Loading /> : tasks.length === 0 ? (
        <EmptyState title="No preparation plan yet" description="Generate one from your profile's target role, or set a role on the Skill Gap page first." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {weeks.map((w) => {
            const weekTasks = tasks.filter((t) => t.week === w).sort((a, b) => a.day - b.day);
            if (weekTasks.length === 0) return null;
            return (
              <div key={w} className="card p-5">
                <h3 className="font-display text-sm font-semibold mb-3">Week {w}</h3>
                <div className="space-y-2.5">
                  {weekTasks.map((t) => (
                    <button key={t.id} onClick={() => toggleTask(t.id)} className="w-full text-left flex items-start gap-2.5 px-3 py-2.5 rounded-lg bg-surfacealt hover:bg-surfacealt/70 transition-colors">
                      {t.completed ? <CheckCircle2 size={16} className="text-mint shrink-0 mt-0.5" /> : <Circle size={16} className="text-muted shrink-0 mt-0.5" />}
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm ${t.completed ? "line-through text-muted" : ""}`}>{t.title}</div>
                        <div className="text-xs text-muted mt-0.5">{t.category} · {t.estimated_minutes} min · {t.difficulty}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
