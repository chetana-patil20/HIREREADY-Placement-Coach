import React from "react";

export default function ProgressBar({ value, label, colorClass = "bg-amber" }) {
  const pct = Math.max(0, Math.min(100, value ?? 0));
  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-xs text-muted mb-1">
          <span>{label}</span>
          <span className="text-text font-medium">{pct}%</span>
        </div>
      )}
      <div className="w-full h-2 rounded-full bg-surfacealt overflow-hidden">
        <div className={`h-full rounded-full ${colorClass}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
