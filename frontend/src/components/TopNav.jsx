import React from "react";
import { LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

export default function TopNav({ title, subtitle }) {
  const { fullName, role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="sticky top-0 z-10 backdrop-blur bg-ink/85 border-b border-border px-6 py-4 flex items-center justify-between">
      <div>
        <h1 className="font-display text-xl font-semibold">{title}</h1>
        {subtitle && <p className="text-sm text-muted mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        <div className="text-right hidden sm:block">
          <div className="text-sm font-medium">{fullName}</div>
          <div className="text-xs text-muted capitalize">{role}</div>
        </div>
        <button onClick={handleLogout} className="btn-secondary flex items-center gap-2 text-sm">
          <LogOut size={15} /> Log out
        </button>
      </div>
    </header>
  );
}
