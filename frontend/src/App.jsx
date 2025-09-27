import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Login } from '@/components/auth/Login';
import { Signup } from '@/components/auth/Signup';
import { ForgotPassword } from '@/components/auth/ForgotPassword';
import { ResetPassword } from '@/components/auth/ResetPassword';
import { VerifyEmail } from '@/components/auth/VerifyEmail';
import './App.css';

// Importar componentes reais
import Dashboard from './components/Dashboard';
import PublicPage from './components/PublicPage';
import Inbox from './components/Inbox';
import MessageDetail from './components/MessageDetail';
import BuyCredits from './components/BuyCredits';
import InstagramStory from './components/InstagramStory';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="App">
          <Routes>
            {/* Rotas públicas */}
            <Route 
              path="/login" 
              element={
                <ProtectedRoute requireAuth={false}>
                  <Login />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/signup" 
              element={
                <ProtectedRoute requireAuth={false}>
                  <Signup />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/forgot-password" 
              element={
                <ProtectedRoute requireAuth={false}>
                  <ForgotPassword />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/reset-password" 
              element={
                <ProtectedRoute requireAuth={false}>
                  <ResetPassword />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/verify-email" 
              element={
                <ProtectedRoute requireAuth={false}>
                  <VerifyEmail />
                </ProtectedRoute>
              } 
            />

            {/* Rotas protegidas */}
            <Route 
              path="/dashboard" 
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/inbox" 
              element={
                <ProtectedRoute>
                  <Inbox />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/messages/:messageId" 
              element={
                <ProtectedRoute>
                  <MessageDetail />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/buy-credits" 
              element={
                <ProtectedRoute>
                  <BuyCredits />
                </ProtectedRoute>
              } 
            />

            {/* Rota padrão */}
            <Route path="/" element={<Navigate to="/login" replace />} />

            {/* Rotas públicas (sem autenticação) - deve vir depois da rota padrão */}
            <Route path="/:slug" element={<PublicPage />} />
            
            {/* Rota 404 */}
            <Route 
              path="*" 
              element={
                <div className="min-h-screen bg-black text-white flex items-center justify-center">
                  <div className="text-center">
                    <h1 className="text-6xl font-bold text-yellow-500 mb-4">404</h1>
                    <p className="text-xl mb-4">Página não encontrada</p>
                    <a href="/" className="text-yellow-500 hover:text-yellow-400">
                      Voltar ao início
                    </a>
                  </div>
                </div>
              } 
            />
          </Routes>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;
