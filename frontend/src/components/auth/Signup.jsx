import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, Mail, Lock, User, Calendar, ArrowRight, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/contexts/AuthContext';
import './Auth.css';

const signupSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string()
    .min(10, 'Senha deve ter pelo menos 10 caracteres')
    .regex(/[A-Z]/, 'Senha deve conter pelo menos uma letra maiúscula')
    .regex(/[a-z]/, 'Senha deve conter pelo menos uma letra minúscula')
    .regex(/[0-9]/, 'Senha deve conter pelo menos um número')
    .regex(/[^A-Za-z0-9]/, 'Senha deve conter pelo menos um símbolo'),
  confirmPassword: z.string(),
  displayName: z.string().min(2, 'Nome deve ter pelo menos 2 caracteres'),
  dob: z.string().refine((date) => {
    const birthDate = new Date(date);
    const today = new Date();
    const age = today.getFullYear() - birthDate.getFullYear();
    return age >= 16;
  }, 'Você deve ter pelo menos 16 anos'),
  acceptTerms: z.boolean().refine(val => val === true, 'Você deve aceitar os termos')
}).refine((data) => data.password === data.confirmPassword, {
  message: "Senhas não coincidem",
  path: ["confirmPassword"]
});

export const Signup = () => {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [passwordStrength, setPasswordStrength] = useState(0);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors }
  } = useForm({
    resolver: zodResolver(signupSchema)
  });

  const password = watch('password', '');

  // Calcular força da senha
  React.useEffect(() => {
    let strength = 0;
    if (password.length >= 10) strength += 25;
    if (/[A-Z]/.test(password)) strength += 25;
    if (/[a-z]/.test(password)) strength += 25;
    if (/[0-9]/.test(password)) strength += 12.5;
    if (/[^A-Za-z0-9]/.test(password)) strength += 12.5;
    setPasswordStrength(strength);
  }, [password]);

  const getPasswordStrengthColor = () => {
    if (passwordStrength < 50) return 'bg-red-500';
    if (passwordStrength < 75) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const getPasswordStrengthText = () => {
    if (passwordStrength < 50) return 'Fraca';
    if (passwordStrength < 75) return 'Média';
    return 'Forte';
  };

  const onSubmit = async (data) => {
    setIsLoading(true);
    setError('');
    setSuccess('');

    const result = await signup({
      email: data.email,
      password: data.password,
      confirmPassword: data.confirmPassword,
      displayName: data.displayName,
      dob: data.dob
    });
    
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

  return (
    <div className="auth-container">
      <div className="auth-background">
        <div className="auth-gradient"></div>
      </div>
      
      <div className="auth-content">
        <Card className="auth-card signup-card">
          <CardHeader className="text-center">
            <div className="auth-logo">
              <div className="logo-circle">
                <span className="logo-text">ANM</span>
              </div>
            </div>
            <CardTitle className="auth-title">Criar conta</CardTitle>
            <CardDescription className="auth-description">
              Junte-se ao ANONYMOUS e comece a receber mensagens anônimas
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
                <Label htmlFor="displayName" className="form-label">
                  <User className="label-icon" />
                  Nome de exibição
                </Label>
                <Input
                  id="displayName"
                  type="text"
                  placeholder="Como você quer ser chamado"
                  className={`form-input ${errors.displayName ? 'error' : ''}`}
                  {...register('displayName')}
                />
                {errors.displayName && (
                  <span className="error-message">{errors.displayName.message}</span>
                )}
              </div>

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
                <Label htmlFor="dob" className="form-label">
                  <Calendar className="label-icon" />
                  Data de nascimento
                </Label>
                <Input
                  id="dob"
                  type="date"
                  className={`form-input ${errors.dob ? 'error' : ''}`}
                  {...register('dob')}
                />
                {errors.dob && (
                  <span className="error-message">{errors.dob.message}</span>
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
                    placeholder="Crie uma senha forte"
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
                
                {password && (
                  <div className="password-strength">
                    <div className="strength-bar">
                      <div 
                        className={`strength-fill ${getPasswordStrengthColor()}`}
                        style={{ width: `${passwordStrength}%` }}
                      ></div>
                    </div>
                    <span className="strength-text">
                      Força: {getPasswordStrengthText()}
                    </span>
                  </div>
                )}

                <div className="password-requirements">
                  <div className={`requirement ${password.length >= 10 ? 'met' : ''}`}>
                    {password.length >= 10 ? <Check size={16} /> : <X size={16} />}
                    Pelo menos 10 caracteres
                  </div>
                  <div className={`requirement ${/[A-Z]/.test(password) ? 'met' : ''}`}>
                    {/[A-Z]/.test(password) ? <Check size={16} /> : <X size={16} />}
                    Uma letra maiúscula
                  </div>
                  <div className={`requirement ${/[a-z]/.test(password) ? 'met' : ''}`}>
                    {/[a-z]/.test(password) ? <Check size={16} /> : <X size={16} />}
                    Uma letra minúscula
                  </div>
                  <div className={`requirement ${/[0-9]/.test(password) ? 'met' : ''}`}>
                    {/[0-9]/.test(password) ? <Check size={16} /> : <X size={16} />}
                    Um número
                  </div>
                  <div className={`requirement ${/[^A-Za-z0-9]/.test(password) ? 'met' : ''}`}>
                    {/[^A-Za-z0-9]/.test(password) ? <Check size={16} /> : <X size={16} />}
                    Um símbolo
                  </div>
                </div>

                {errors.password && (
                  <span className="error-message">{errors.password.message}</span>
                )}
              </div>

              <div className="form-group">
                <Label htmlFor="confirmPassword" className="form-label">
                  <Lock className="label-icon" />
                  Confirmar senha
                </Label>
                <div className="password-input-container">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirme sua senha"
                    className={`form-input password-input ${errors.confirmPassword ? 'error' : ''}`}
                    {...register('confirmPassword')}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  >
                    {showConfirmPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <span className="error-message">{errors.confirmPassword.message}</span>
                )}
              </div>

              <div className="form-group">
                <div className="checkbox-container">
                  <Checkbox 
                    id="acceptTerms"
                    {...register('acceptTerms')}
                  />
                  <Label htmlFor="acceptTerms" className="checkbox-label">
                    Li e aceito os{' '}
                    <Link to="/terms" className="auth-link">
                      Termos de Uso
                    </Link>
                    {' '}e a{' '}
                    <Link to="/privacy" className="auth-link">
                      Política de Privacidade
                    </Link>
                  </Label>
                </div>
                {errors.acceptTerms && (
                  <span className="error-message">{errors.acceptTerms.message}</span>
                )}
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
                    Criar conta
                    <ArrowRight className="button-icon" />
                  </>
                )}
              </Button>

              <div className="auth-divider">
                <span>ou</span>
              </div>

              <div className="auth-footer">
                <p>
                  Já tem uma conta?{' '}
                  <Link to="/login" className="auth-link">
                    Fazer login
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
