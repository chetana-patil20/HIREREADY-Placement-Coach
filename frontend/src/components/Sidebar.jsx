import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Briefcase, Target, ListChecks, MessageSquareText,
  FileText, Mic, Bell, CalendarDays, GraduationCap, LifeBuoy, ShieldCheck, User,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const studentLinks = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/placements", label: "Placements", icon: Briefcase },
  { to: "/skill-gap", label: "Skill Gap", icon: Target },
  { to: "/preparation-plan", label: "Prep Plan", icon: ListChecks },
  { to: "/mock-interview", label: "Mock Interview", icon: Mic },
  { to: "/resume-analyzer", label: "Resume Analyzer", icon: FileText },
  { to: "/ai-coach", label: "AI Coach", icon: MessageSquareText },
  { to: "/notifications", label: "Notifications", icon: Bell },
  { to: "/events", label: "Events", icon: CalendarDays },
  { to: "/academics", label: "Academics", icon: GraduationCap },
  { to: "/support", label: "Support", icon: LifeBuoy },
  { to: "/profile", label: "Profile", icon: User },
];

const adminLinks = [
  { to: "/admin", label: "Admin Dashboard", icon: ShieldCheck },
  { to: "/admin/placements", label: "Manage Placements", icon: Briefcase },
  { to: "/admin/support", label: "Support Tickets", icon: LifeBuoy },
];

export default function Sidebar() {
  const { role } = useAuth();
  const links = role === "admin" ? adminLinks : studentLinks;

  return (
    <aside className="hidden md:flex md:flex-col w-60 shrink-0 border-r border-border bg-surface min-h-screen sticky top-0">
      <div className="px-5 py-5 border-b border-border">
        <div className="font-display text-lg font-semibold tracking-tight">HireReady</div>
        <div className="text-xs text-muted mt-0.5">Intelligent Placement Coach</div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive ? "bg-amber/10 text-amber" : "text-muted hover:text-text hover:bg-surfacealt"
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
