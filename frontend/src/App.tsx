import { Routes, Route, Navigate } from "react-router-dom";
import LoginPage from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import JDManagement from "./pages/JDManagement";
import Candidates from "./pages/Candidates";
import Matching from "./pages/Matching";
import MatchHistory from "./pages/MatchHistory";
import Settings from "./pages/Settings";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

export default function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected routes with layout shell */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/jd" element={<JDManagement />} />
          <Route path="/candidates" element={<Candidates />} />
          <Route path="/matching/:jdId" element={<Matching />} />
          <Route path="/matching" element={<Matching />} />
          <Route path="/match-history" element={<MatchHistory />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Route>

      {/* Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
