import React, { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Check, X, Mail, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import './Auth.css';

export const VerifyEmail = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchParams] = useSearchParams();
  const { verifyEmail } = useAuth();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  useEffect(() => {
    const verify = async () => {
      if (!token) {
        setError('Token de verificação inválido');
        setIsLoading(false);
        return;
      }

      const result = await verifyEmail(token);
      
      if (result.success) {
        setSuccess(result.message);
        setTimeout(() => {
          navigate('/login');
        }, 3000);
      } else {
        setError(result.error);
      }
      
      setIsLoading(false);
    };

    verify();
  }, [token, verifyEmail, navigate]);

  return (
    <div className="auth-container">
      <div className="auth-background">
        <div className="auth-gradient"></div>
      </div>
      
      <div className="auth-content">
        <Card className="auth-card">
          <CardHeader className="text-center">
            <div className="auth-logo">
              <div className="logo-circle">
                <span className="logo-text">ANM</span>
              </div>
            </div>
            <CardTitle className="auth-title">
              {isLoading ? 'Verificando email...' : success ? 'Email verificado!' : 'Erro na verificação'}
            </CardTitle>
            <CardDescription className="auth-description">
              {isLoading && 'Aguarde enquanto verificamos seu email'}
              {success && 'Sua conta foi ativada com sucesso'}
              {error && 'Não foi possível verificar seu email'}
            </CardDescription>
          </CardHeader>
          
          <CardContent className="text-center">
            {isLoading && (
              <div className="flex justify-center mb-6">
                <div className="loading-spinner"></div>
              </div>
            )}

            {success && (
              <>
                <div className="flex justify-center mb-6">
                  <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center">
                    <Check className="w-8 h-8 text-white" />
                  </div>
                </div>
                <Alert className="mb-6 border-green-500 text-green-700">
                  <Check className="h-4 w-4" />
                  <AlertDescription>{success}</AlertDescription>
                </Alert>
                <p className="text-sm text-gray-400 mb-6">
                  Você será redirecionado para o login em alguns segundos...
                </p>
              </>
            )}

            {error && (
              <>
                <div className="flex justify-center mb-6">
                  <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center">
                    <X className="w-8 h-8 text-white" />
                  </div>
                </div>
                <Alert variant="destructive" className="mb-6">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              </>
            )}

            <div className="space-y-4">
              {success && (
                <Button 
                  onClick={() => navigate('/login')}
                  className="auth-button w-full"
                >
                  Ir para o login
                  <ArrowRight className="button-icon" />
                </Button>
              )}

              {error && (
                <div className="space-y-2">
                  <Button 
                    onClick={() => window.location.href = '/signup'}
                    className="auth-button w-full"
                  >
                    Criar nova conta
                    <Mail className="button-icon" />
                  </Button>
                  <Link to="/login" className="auth-link block">
                    Voltar ao login
                  </Link>
                </div>
              )}

              {!error && !success && !isLoading && (
                <Link to="/login" className="auth-link">
                  Voltar ao login
                </Link>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
