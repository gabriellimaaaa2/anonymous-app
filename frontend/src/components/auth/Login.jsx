import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import './Auth.css';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(1, 'Senha é obrigatória')
});

export const Login = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm({
    resolver: zodResolver(loginSchema)
  });

  const onSubmit = async (data) => {
    setIsLoading(true);
    setError('');

    const result = await login(data.email, data.password);
    
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

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
            <CardTitle className="auth-title">Bem-vindo de volta</CardTitle>
            <CardDescription className="auth-description">
              Entre na sua conta para acessar suas mensagens anônimas
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="auth-form">
              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="form-group">
                <Label htmlFor="email" className="form-label">
                  <Mail className="label-icon" />
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com"
                  className={`form-input ${errors.email ? 'error' : ''}`}
                  {...register('email')}
                />
                {errors.email && (
                  <span className="error-message">{errors.email.message}</span>
                )}
              </div>

              <div className="form-group">
                <Label htmlFor="password" className="form-label">
                  <Lock className="label-icon" />
                  Senha
                </Label>
                <div className="password-input-container">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Sua senha"
                    className={`form-input password-input ${errors.password ? 'error' : ''}`}
                    {...register('password')}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {errors.password && (
                  <span className="error-message">{errors.password.message}</span>
                )}
              </div>

              <div className="form-actions">
                <Link to="/forgot-password" className="forgot-link">
                  Esqueceu sua senha?
                </Link>
              </div>

              <Button 
                type="submit" 
                className="auth-button"
                disabled={isLoading}
              >
                {isLoading ? (
                  <div className="loading-spinner"></div>
                ) : (
                  <>
                    Entrar
                    <ArrowRight className="button-icon" />
                  </>
                )}
              </Button>

              <div className="auth-divider">
                <span>ou</span>
              </div>

              <div className="auth-footer">
                <p>
                  Não tem uma conta?{' '}
                  <Link to="/signup" className="auth-link">
                    Criar conta
                  </Link>
                </p>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
