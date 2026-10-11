import React from "react";
import { Loader2 } from "lucide-react";

export default function Loading({ label = "Loading..." }) {
  return (
    <div className="flex items-center gap-2 text-muted text-sm py-10 justify-center">
      <Loader2 size={16} className="animate-spin" />
      {label}
    </div>
  );
}
