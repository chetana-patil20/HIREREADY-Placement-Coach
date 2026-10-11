import React, { useEffect, useState } from "react";
import { Bell, Clock, Briefcase, ListChecks, Megaphone } from "lucide-react";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import api from "../services/api";

const ICONS = { deadline: Clock, drive: Briefcase, task: ListChecks, announcement: Megaphone, eligibility: Bell, interview: Bell, general: Bell };

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/notifications").then((res) => setItems(res.data)).finally(() => setLoading(false));
  }, []);

  return (
    <Layout title="Notifications" subtitle="Generated from real deadlines, drives, and task data — nothing here is invented.">
      {loading ? <Loading /> : items.length === 0 ? (
        <EmptyState title="You're all caught up" description="No notifications right now." />
      ) : (
        <div className="space-y-3">
          {items.map((n, i) => {
            const Icon = ICONS[n.category] || Bell;
            return (
              <div key={i} className="card p-4 flex items-start gap-3">
                <Icon size={17} className="text-amber shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-medium">{n.title}</div>
                  <p className="text-xs text-muted mt-0.5">{n.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
