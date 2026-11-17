import React from 'react';
import { Navigate } from 'react-router-dom';
import { isAuthenticated, getCurrentUser } from '../api.js';

export default function ProtectedRoute({ children, requiredRole }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const user = getCurrentUser();
    if (!user || user.role !== requiredRole) {
      // Show inline 403 rather than redirect, so AuditPage can handle it too
      return (
        <div className="min-h-screen bg-brand-bg flex items-center justify-center p-4">
          <div className="bg-brand-card border border-brand-border rounded-xl p-8 text-center max-w-md shadow-card">
            <div className="text-brand-danger text-4xl mb-4">🚫</div>
            <h2 className="text-brand-textPrimary text-xl font-bold mb-2">Access Denied</h2>
            <p className="text-brand-textSecondary text-xs">
              You need <span className="text-brand-danger font-semibold">{requiredRole}</span> role to access this page.
            </p>
            <p className="text-brand-textMuted mt-2 text-xs font-mono">
              Your current role: <span className="text-brand-textPrimary">{getCurrentUser()?.role ?? 'unknown'}</span>
            </p>
            <a href="/" className="mt-6 inline-block text-brand-secondary hover:text-white underline text-xs font-semibold">
              ← Back to Dashboard
            </a>
          </div>
        </div>
      );
    }
  }

  return children;
}
