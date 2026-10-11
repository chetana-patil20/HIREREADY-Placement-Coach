import React from "react";

export default function EmptyState({ title, description, action }) {
  return (
    <div className="card px-6 py-10 text-center">
      <div className="font-display text-base font-medium">{title}</div>
      {description && <p className="text-sm text-muted mt-1.5 max-w-md mx-auto">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
