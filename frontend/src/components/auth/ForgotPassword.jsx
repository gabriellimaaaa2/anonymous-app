import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Mail, ArrowLeft, Send, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import './Auth.css';

const forgotPasswordSchema = z.object({
  email: z.string().email('Email inválido')
});

export const ForgotPassword = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { forgotPassword } = useAuth();

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm({
    resolver: zodResolver(forgotPasswordSchema)
  });

  const onSubmit = async (data) => {
    setIsLoading(true);
    setError('');
    setSuccess('');

    const result = await forgotPassword(data.email);
    
    if (result.success) {
      setSuccess(result.message);
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
            <CardTitle className="auth-title">Recuperar senha</CardTitle>
            <CardDescription className="auth-description">
              Digite seu email para receber um link de recuperação de senha
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            <form onSubmit={handleSubmit(onSubmit)} className="auth-form">
              {error && (
                <Alert variant="destructive" className="mb-4">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="mb-4 border-green-500 text-green-700">
                  <Check className="h-4 w-4" />
                  <AlertDescription>{success}</AlertDescription>
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

              <Button 
                type="submit" 
                className="auth-button"
                disabled={isLoading || success}
              >
                {isLoading ? (
                  <div className="loading-spinner"></div>
                ) : success ? (
                  <>
                    Email enviado
                    <Check className="button-icon" />
                  </>
                ) : (
                  <>
                    Enviar link
                    <Send className="button-icon" />
                  </>
                )}
              </Button>

              <div className="auth-footer">
                <Link to="/login" className="auth-link flex items-center gap-2">
                  <ArrowLeft size={16} />
                  Voltar ao login
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
