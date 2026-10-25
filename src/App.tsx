import { Navigate, Route, Routes } from "react-router-dom";
import PublicLayout from "./components/PublicLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import DeveloperPage from "./pages/DeveloperPage";
import PrivacyPolicyPage from "./pages/PrivacyPolicyPage";
import WorkspacePage from "./pages/WorkspacePage";

export default function App() {
  return (
    <Routes>
      <Route path="/auth" element={<AuthPage />} />
      <Route path="/signup" element={<AuthPage />} />
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/privacy-policy" element={<PrivacyPolicyPage />} />
        <Route path="/developer" element={<DeveloperPage />} />
      </Route>
      <Route
        path="/app/learner"
        element={
          <ProtectedRoute requiredRole="learner">
            <WorkspacePage role="learner" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/facilitator"
        element={
          <ProtectedRoute requiredRole="facilitator">
            <WorkspacePage role="facilitator" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/supervisor"
        element={
          <ProtectedRoute requiredRole="supervisor">
            <WorkspacePage role="supervisor" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/app/administrator"
        element={
          <ProtectedRoute requiredRole="administrator">
            <WorkspacePage role="administrator" />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
