import React, { useEffect, useState } from "react";
import { CalendarDays, MapPin } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import StatusChip from "../components/StatusChip";
import api from "../services/api";

const CATEGORIES = ["all", "hackathon", "workshop", "seminar", "placement", "career"];

export default function Events() {
  const [events, setEvents] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [category, setCategory] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.get("/api/events"), api.get("/api/announcements")]).then(([e, a]) => {
      setEvents(e.data);
      setAnnouncements(a.data);
      setLoading(false);
    });
  }, []);

  const filtered = category === "all" ? events : events.filter((e) => e.category === category);

  if (loading) return <Layout title="Events & announcements"><Loading /></Layout>;

  return (
    <Layout title="Events & announcements" subtitle="Hackathons, workshops, seminars, and placement events.">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2">
          <div className="flex gap-2 mb-4 flex-wrap">
            {CATEGORIES.map((c) => (
              <button key={c} onClick={() => setCategory(c)} className={`px-3 py-1.5 rounded-full text-xs border capitalize transition-colors ${category === c ? "border-amber text-amber bg-amber/10" : "border-border text-muted"}`}>
                {c}
              </button>
            ))}
          </div>
          <div className="space-y-3">
            {filtered.map((e) => (
              <div key={e.id} className="card p-5">
                <div className="flex items-start justify-between mb-1">
                  <h3 className="font-display text-sm font-semibold">{e.title}</h3>
                  <StatusChip label={e.category} variant="neutral" />
                </div>
                <p className="text-sm text-muted mb-2">{e.description}</p>
                <div className="flex gap-4 text-xs text-muted">
                  {e.event_date && <span className="flex items-center gap-1"><CalendarDays size={12} /> {e.event_date}</span>}
                  {e.location && <span className="flex items-center gap-1"><MapPin size={12} /> {e.location}</span>}
                </div>
              </div>
            ))}
            {filtered.length === 0 && <p className="text-sm text-muted">No events in this category.</p>}
          </div>
        </div>

        <div>
          <h3 className="font-display text-sm font-semibold mb-3">Announcements</h3>
          <div className="space-y-3">
            {announcements.map((a) => (
              <div key={a.id} className="card p-4">
                <div className="text-sm font-medium">{a.title}</div>
                <p className="text-xs text-muted mt-1">{a.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Layout>
  );
}
