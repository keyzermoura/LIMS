import type { ReactNode } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Loader2 } from "lucide-react";

import { Layout } from "@/components/layout/Layout";
import { useAuth } from "@/hooks/use-auth";
import { AuditTrailPage } from "@/pages/AuditTrail";
import { CapasPage } from "@/pages/Capas";
import { CoordinationReviewsPage } from "@/pages/CoordinationReviews";
import { DashboardPage } from "@/pages/Dashboard";
import { LoginPage } from "@/pages/Login";
import { ReceiptsPage } from "@/pages/Receipts";
import { SolicitationsPage } from "@/pages/Solicitations";
import { TestsPage } from "@/pages/Tests";

function FullScreenLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
        <p className="text-sm">Verificando sessão…</p>
      </div>
    </div>
  );
}

function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") return <FullScreenLoader />;
  if (status === "anonymous") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}

function LoginRoute() {
  const { status } = useAuth();
  if (status === "loading") return <FullScreenLoader />;
  if (status === "authenticated") return <Navigate to="/" replace />;
  return <LoginPage />;
}

function AuditRoute() {
  const { user } = useAuth();
  const allowed = user?.role === "ADMIN" || user?.role === "AUDITOR";
  return allowed ? <AuditTrailPage /> : <Navigate to="/" replace />;
}

function CoordinationRoute() {
  const { user } = useAuth();
  const allowed = user?.role === "ADMIN" || user?.role === "FISCAL";
  return allowed ? <CoordinationReviewsPage /> : <Navigate to="/" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="/solicitations" element={<SolicitationsPage />} />
        <Route path="/receipts" element={<ReceiptsPage />} />
        <Route path="/coordination-reviews" element={<CoordinationRoute />} />
        <Route path="/tests" element={<TestsPage />} />
        <Route path="/capas" element={<CapasPage />} />
        <Route path="/audit" element={<AuditRoute />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
