import React from "react";
import Sidebar from "./Sidebar";
import TopNav from "./TopNav";

export default function Layout({ title, subtitle, children }) {
  return (
    <div className="flex min-h-screen bg-ink text-text">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <TopNav title={title} subtitle={subtitle} />
        <main className="p-6 max-w-7xl mx-auto">{children}</main>
      </div>
    </div>
  );
}
