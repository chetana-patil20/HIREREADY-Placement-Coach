import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, requireRole }) {
  const { isAuthenticated, role } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (requireRole && role !== requireRole) {
    return <Navigate to={role === "admin" ? "/admin" : "/dashboard"} replace />;
  }
  return children;
}
