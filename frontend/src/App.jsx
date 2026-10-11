import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import Placements from "./pages/Placements";
import PlacementDetail from "./pages/PlacementDetail";
import SkillGap from "./pages/SkillGap";
import PreparationPlan from "./pages/PreparationPlan";
import MockInterview from "./pages/MockInterview";
import ResumeAnalyzer from "./pages/ResumeAnalyzer";
import AICoach from "./pages/AICoach";
import Notifications from "./pages/Notifications";
import Events from "./pages/Events";
import Academics from "./pages/Academics";
import Support from "./pages/Support";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminPlacements from "./pages/admin/AdminPlacements";
import AdminSupport from "./pages/admin/AdminSupport";
import { useAuth } from "./context/AuthContext";

export default function App() {
  const { isAuthenticated, role } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />

      <Route path="/dashboard" element={<ProtectedRoute requireRole="student"><Dashboard /></ProtectedRoute>} />
      <Route path="/profile" element={<ProtectedRoute requireRole="student"><Profile /></ProtectedRoute>} />
      <Route path="/placements" element={<ProtectedRoute requireRole="student"><Placements /></ProtectedRoute>} />
      <Route path="/placements/:id" element={<ProtectedRoute requireRole="student"><PlacementDetail /></ProtectedRoute>} />
      <Route path="/skill-gap" element={<ProtectedRoute requireRole="student"><SkillGap /></ProtectedRoute>} />
      <Route path="/preparation-plan" element={<ProtectedRoute requireRole="student"><PreparationPlan /></ProtectedRoute>} />
      <Route path="/mock-interview" element={<ProtectedRoute requireRole="student"><MockInterview /></ProtectedRoute>} />
      <Route path="/resume-analyzer" element={<ProtectedRoute requireRole="student"><ResumeAnalyzer /></ProtectedRoute>} />
      <Route path="/ai-coach" element={<ProtectedRoute requireRole="student"><AICoach /></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute requireRole="student"><Notifications /></ProtectedRoute>} />
      <Route path="/events" element={<ProtectedRoute requireRole="student"><Events /></ProtectedRoute>} />
      <Route path="/academics" element={<ProtectedRoute requireRole="student"><Academics /></ProtectedRoute>} />
      <Route path="/support" element={<ProtectedRoute requireRole="student"><Support /></ProtectedRoute>} />

      <Route path="/admin" element={<ProtectedRoute requireRole="admin"><AdminDashboard /></ProtectedRoute>} />
      <Route path="/admin/placements" element={<ProtectedRoute requireRole="admin"><AdminPlacements /></ProtectedRoute>} />
      <Route path="/admin/support" element={<ProtectedRoute requireRole="admin"><AdminSupport /></ProtectedRoute>} />

      <Route
        path="/"
        element={
          isAuthenticated ? <Navigate to={role === "admin" ? "/admin" : "/dashboard"} replace /> : <Navigate to="/login" replace />
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
