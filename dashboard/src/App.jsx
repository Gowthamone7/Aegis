import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from './components/AppLayout.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';

import LoginPage from './pages/LoginPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import IncidentsPage from './pages/IncidentsPage.jsx';
import PipelinePage from './pages/PipelinePage.jsx';
import KnowledgePage from './pages/KnowledgePage.jsx';
import ApprovalsPage from './pages/ApprovalsPage.jsx';
import CodeGuardPage from './pages/CodeGuardPage.jsx';
import AuditPage from './pages/AuditPage.jsx';
import PolicyPage from './pages/PolicyPage.jsx';
import OrganizationsPage from './pages/OrganizationsPage.jsx';
import SettingsPage from './pages/SettingsPage.jsx';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout>
                <DashboardPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/incidents"
          element={
            <ProtectedRoute>
              <AppLayout>
                <IncidentsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/pipeline"
          element={
            <ProtectedRoute>
              <AppLayout>
                <PipelinePage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/knowledge"
          element={
            <ProtectedRoute>
              <AppLayout>
                <KnowledgePage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/approvals"
          element={
            <ProtectedRoute>
              <AppLayout>
                <ApprovalsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/codeguard"
          element={
            <ProtectedRoute>
              <AppLayout>
                <CodeGuardPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/audit"
          element={
            <ProtectedRoute>
              <AppLayout>
                <AuditPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/policy"
          element={
            <ProtectedRoute>
              <AppLayout>
                <PolicyPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/organizations"
          element={
            <ProtectedRoute>
              <AppLayout>
                <OrganizationsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <AppLayout>
                <SettingsPage />
              </AppLayout>
            </ProtectedRoute>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
