import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  // Configurar axios com interceptors
  useEffect(() => {
    const token = Cookies.get('auth_token');
    if (token) {
      setToken(token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    // Interceptor para respostas
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Verificar se o usuário está autenticado ao carregar a aplicação
  useEffect(() => {
    const checkAuth = async () => {
      const token = Cookies.get('auth_token');
      if (token) {
        try {
          const response = await axios.get('/api/auth/me');
          setUser(response.data.user);
          setToken(token);
        } catch (error) {
          console.error('Erro ao verificar autenticação:', error);
          logout();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email, password) => {
    try {
      const response = await axios.post('/api/auth/login', {
        email,
        password
      });

      const { token, user } = response.data;
      
      // Salvar token no cookie (7 dias)
      Cookies.set('auth_token', token, { expires: 7, secure: true, sameSite: 'strict' });
      
      // Configurar header de autorização
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setToken(token);
      setUser(user);
      
      return { success: true, user };
    } catch (error) {
      console.error('Erro no login:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erro ao fazer login' 
      };
    }
  };

  const signup = async (userData) => {
    try {
      const response = await axios.post('/api/auth/signup', userData);
      
      return { 
        success: true, 
        message: response.data.message || 'Conta criada com sucesso! Verifique seu email.' 
      };
    } catch (error) {
      console.error('Erro no signup:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erro ao criar conta' 
      };
    }
  };

  const logout = () => {
    Cookies.remove('auth_token');
    delete axios.defaults.headers.common['Authorization'];
    setToken(null);
    setUser(null);
  };

  const forgotPassword = async (email) => {
    try {
      const response = await axios.post('/api/auth/forgot-password', { email });
      return { 
        success: true, 
        message: response.data.message || 'Email de recuperação enviado!' 
      };
    } catch (error) {
      console.error('Erro ao solicitar recuperação:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erro ao enviar email de recuperação' 
      };
    }
  };

  const resetPassword = async (token, newPassword) => {
    try {
      const response = await axios.post('/api/auth/reset-password', {
        token,
        password: newPassword
      });
      return { 
        success: true, 
        message: response.data.message || 'Senha alterada com sucesso!' 
      };
    } catch (error) {
      console.error('Erro ao redefinir senha:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erro ao redefinir senha' 
      };
    }
  };

  const verifyEmail = async (token) => {
    try {
      const response = await axios.post('/api/auth/verify-email', { token });
      return { 
        success: true, 
        message: response.data.message || 'Email verificado com sucesso!' 
      };
    } catch (error) {
      console.error('Erro ao verificar email:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erro ao verificar email' 
      };
    }
  };

  const updateProfile = async (profileData) => {
    try {
      const response = await axios.put('/api/user/profile', profileData);
      setUser(response.data.user);
      return { 
        success: true, 
        message: 'Perfil atualizado com sucesso!' 
      };
    } catch (error) {
      console.error('Erro ao atualizar perfil:', error);
      return { 
        success: false, 
        error: error.response?.data?.message || 'Erro ao atualizar perfil' 
      };
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    signup,
    logout,
    forgotPassword,
    resetPassword,
    verifyEmail,
    updateProfile,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
