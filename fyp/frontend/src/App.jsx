import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Chat from "./pages/Chat";
import Documents from "./pages/Documents";
import SearchPage from "./pages/SearchPage";
import HistoryPage from "./pages/HistoryPage";
import Evaluation from "./pages/Evaluation";
import Settings from "./pages/Settings";

function RequireAuth({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/evaluation" element={<Evaluation />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
