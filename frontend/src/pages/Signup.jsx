import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { GraduationCap } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export default function Signup() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [verificationPending, setVerificationPending] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register, verifyEmail } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await register(fullName, email, password);
      setVerificationPending(true);
      showToast(data.message, "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Sign up failed.", "error");
    } finally { setLoading(false); }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await verifyEmail(email, verificationCode);
      showToast("Email verified. Your account is ready.", "success");
      navigate(data.role === "admin" ? "/admin" : "/dashboard");
    } catch (err) {
      showToast(err.response?.data?.detail || "Email verification failed.", "error");
    } finally { setLoading(false); }
  };

  const resendCode = async () => {
    setLoading(true);
    try {
      const data = await register(fullName, email, password);
      setVerificationCode("");
      showToast(data.message, "success");
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not resend the code.", "error");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ink text-text px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 mb-8 justify-center"><GraduationCap className="text-amber" size={26} /><span className="font-display text-2xl font-semibold">HireReady</span></div>
        <div className="card p-6">
          <h1 className="font-display text-lg font-semibold mb-1">{verificationPending ? "Verify your email" : "Create your account"}</h1>
          <p className="text-sm text-muted mb-6">{verificationPending ? `Enter the 6-digit code sent to ${email}.` : "Start tracking your placement readiness today."}</p>
          {verificationPending ? <form onSubmit={handleVerify} className="space-y-4">
            <div><label className="text-xs text-muted mb-1 block">Verification code</label><input className="input-field" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength={6} value={verificationCode} onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ""))} required /></div>
            <button className="btn-primary w-full" type="submit" disabled={loading || verificationCode.length !== 6}>{loading ? "Verifying..." : "Verify email and continue"}</button>
            <button className="text-sm text-amber w-full" type="button" onClick={resendCode} disabled={loading}>{loading ? "Please wait..." : "Send a new code"}</button>
          </form> : <form onSubmit={handleSubmit} className="space-y-4">
            <div><label className="text-xs text-muted mb-1 block">Full name</label><input className="input-field" autoComplete="name" value={fullName} onChange={(e) => setFullName(e.target.value)} required maxLength={120} /></div>
            <div><label className="text-xs text-muted mb-1 block">Email</label><input className="input-field" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></div>
            <div><label className="text-xs text-muted mb-1 block">Password</label><input className="input-field" type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} maxLength={72} /></div>
            <button className="btn-primary w-full" type="submit" disabled={loading}>{loading ? "Sending verification code..." : "Create account"}</button>
          </form>}
        </div>
        <p className="text-sm text-muted text-center mt-5">Already have an account? <Link to="/login" className="text-amber">Log in</Link></p>
      </div>
    </div>
  );
}
