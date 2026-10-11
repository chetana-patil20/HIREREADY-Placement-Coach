import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import api from "../services/api";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export default function Academics() {
  const [timetable, setTimetable] = useState([]);
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get("/api/timetable"), api.get("/api/exams")]).then(([t, e]) => {
      setTimetable(t.data);
      setExams(e.data);
      setLoading(false);
    });
  }, []);

  if (loading) return <Layout title="Academics"><Loading /></Layout>;

  const nearestExam = exams[0];

  return (
    <Layout title="Academics" subtitle="Supports your placement journey — your prep plan adjusts around these dates.">
      {nearestExam && (
        <div className="card p-4 mb-5 border-amber/40 bg-amber/5 text-sm">
          Your next exam ({nearestExam.subject}) is on <span className="text-amber font-medium">{nearestExam.exam_date}</span>. Plan your daily study hours around it.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Weekly timetable</h3>
          <div className="space-y-4">
            {DAYS.map((day) => {
              const rows = timetable.filter((t) => t.day_of_week === day);
              if (rows.length === 0) return null;
              return (
                <div key={day}>
                  <div className="text-xs text-muted mb-1.5">{day}</div>
                  <div className="space-y-1.5">
                    {rows.map((r) => (
                      <div key={r.id} className="flex justify-between text-sm bg-surfacealt rounded-lg px-3 py-2">
                        <span>{r.subject}</span>
                        <span className="text-muted">{r.start_time} – {r.end_time} · {r.room}</span>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="card p-6">
          <h3 className="font-display text-sm font-semibold mb-4">Exam schedule</h3>
          <div className="space-y-2.5">
            {exams.map((e) => (
              <div key={e.id} className="flex justify-between text-sm">
                <span>{e.subject}</span>
                <span className="text-muted">{e.exam_date}</span>
              </div>
            ))}
            {exams.length === 0 && <p className="text-sm text-muted">No exams scheduled.</p>}
          </div>
        </div>
      </div>
    </Layout>
  );
}
