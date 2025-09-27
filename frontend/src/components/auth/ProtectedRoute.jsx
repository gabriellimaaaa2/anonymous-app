import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export const ProtectedRoute = ({ children, requireAuth = true }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-center">
          <div className="auth-logo mb-4">
            <div className="logo-circle">
              <span className="logo-text">ANM</span>
            </div>
          </div>
          <div className="loading-spinner mx-auto"></div>
          <p className="text-white mt-4">Carregando...</p>
        </div>
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    // Salvar a localização atual para redirecionar após o login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!requireAuth && isAuthenticated) {
    // Se o usuário já está logado e tenta acessar páginas de auth, redirecionar para dashboard
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};
