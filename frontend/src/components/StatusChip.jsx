import React from "react";

const STYLES = {
  eligible: "bg-mint/15 text-mint border-mint/40",
  "not-eligible": "bg-coral/15 text-coral border-coral/40",
  strong: "bg-mint/15 text-mint border-mint/40",
  "needs improvement": "bg-amber/15 text-amber border-amber/40",
  missing: "bg-coral/15 text-coral border-coral/40",
  pending: "bg-amber/15 text-amber border-amber/40",
  "in progress": "bg-blue-400/15 text-blue-300 border-blue-400/40",
  resolved: "bg-mint/15 text-mint border-mint/40",
  neutral: "bg-surfacealt text-muted border-border",
};

export default function StatusChip({ label, variant = "neutral" }) {
  const key = (variant || "neutral").toLowerCase();
  const cls = STYLES[key] || STYLES.neutral;
  return (
    <span className={`inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-full border ${cls}`}>
      {label}
    </span>
  );
}
