import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GraduationCap } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export default function Login() {
  const [email, setEmail] = useState("demo.student@hireready.app");
  const [password, setPassword] = useState("Demo@1234");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await login(email, password);
      showToast("Welcome back!", "success");
      navigate(data.role === "admin" ? "/admin" : "/dashboard");
    } catch (err) {
      showToast(err.response?.data?.detail || "Login failed.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink text-text px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 mb-8 justify-center">
          <GraduationCap className="text-amber" size={26} />
          <span className="font-display text-2xl font-semibold">HireReady</span>
        </div>
        <div className="card p-6">
          <h1 className="font-display text-lg font-semibold mb-1">Log in</h1>
          <p className="text-sm text-muted mb-6">Continue your placement preparation.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs text-muted mb-1 block">Email</label>
              <input className="input-field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <label className="text-xs text-muted mb-1 block">Password</label>
              <input className="input-field" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <button className="btn-primary w-full" type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Log in"}
            </button>
          </form>
          <p className="text-xs text-muted mt-4 leading-relaxed">
            Demo student: demo.student@hireready.app / Demo@1234<br />
            Demo admin: admin@hireready.app / Admin@1234
          </p>
        </div>
        <p className="text-sm text-muted text-center mt-5">
          New here? <Link to="/signup" className="text-amber">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
