import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import JDManagement from "./pages/JDManagement";
import Candidates from "./pages/Candidates";
import Matching from "./pages/Matching";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/jd" element={<JDManagement />} />
      <Route path="/candidates" element={<Candidates />} />
      <Route path="/matching" element={<Matching />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
