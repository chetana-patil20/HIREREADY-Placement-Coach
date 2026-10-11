import React, { createContext, useContext, useState } from "react";
import api from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem("hireready_token"));
  const [role, setRole] = useState(localStorage.getItem("hireready_role"));
  const [fullName, setFullName] = useState(localStorage.getItem("hireready_name") || "");

  const login = async (email, password) => {
    const res = await api.post("/api/auth/login", { email, password });
    persistSession(res.data);
    return res.data;
  };

  const register = async (full_name, email, password) => {
    const res = await api.post("/api/auth/register", { full_name, email, password });
    return res.data;
  };

  const verifyEmail = async (email, code) => {
    const res = await api.post("/api/auth/verify-email", { email, code });
    persistSession(res.data);
    return res.data;
  };

  const persistSession = (data) => {
    localStorage.setItem("hireready_token", data.access_token);
    localStorage.setItem("hireready_role", data.role);
    localStorage.setItem("hireready_name", data.full_name);
    setToken(data.access_token);
    setRole(data.role);
    setFullName(data.full_name);
  };

  const logout = () => {
    const currentToken = localStorage.getItem("hireready_token");
    localStorage.removeItem("hireready_token");
    localStorage.removeItem("hireready_role");
    localStorage.removeItem("hireready_name");
    setToken(null);
    setRole(null);
    setFullName("");
    if (currentToken) {
      api.post("/api/auth/logout", {}, { headers: { Authorization: `Bearer ${currentToken}` } }).catch(() => {});
    }
  };

  return (
    <AuthContext.Provider value={{ token, role, fullName, login, register, verifyEmail, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
