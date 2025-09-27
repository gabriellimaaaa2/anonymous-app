import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, MapPin, Shield, Heart, MessageCircle, Instagram, Share2 } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const PublicPage = () => {
  const { slug } = useParams();
  const navigate = useNavigate();
  
  const [user, setUser] = useState(null);
  const [message, setMessage] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (slug) {
      fetchUserProfile();
      fetchUserStats();
    }
  }, [slug]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API_BASE}/public/${slug}`);
      setUser(response.data.user);
    } catch (error) {
      if (error.response?.status === 404) {
        setError('Usuário não encontrado');
      } else {
        setError('Erro ao carregar perfil');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUserStats = async () => {
    try {
      const response = await axios.get(`${API_BASE}/public/${slug}/stats`);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!message.trim()) {
      setError('Digite uma mensagem');
      return;
    }

    if (message.length > 5000) {
      setError('Mensagem muito longa (máximo 5000 caracteres)');
      return;
    }

    setIsSending(true);
    setError('');

    try {
      const response = await axios.post(`${API_BASE}/public/${slug}/send`, {
        text: message.trim()
      });

      setMessage('');
      setShowSuccess(true);
      
      // Atualizar estatísticas
      fetchUserStats();
      
      setTimeout(() => {
        setShowSuccess(false);
      }, 5000);

    } catch (error) {
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Erro ao enviar mensagem. Tente novamente.');
      }
    } finally {
      setIsSending(false);
    }
  };

  const handleShareInstagram = () => {
    const text = `Mande uma mensagem anônima para mim! 🕵️‍♂️`;
    const url = window.location.href;
    
    // Tentar abrir o Instagram (mobile)
    const instagramUrl = `instagram://story-camera`;
    
    // Fallback para web
    const webUrl = `https://www.instagram.com/`;
    
    // Copiar link para clipboard
    navigator.clipboard.writeText(url).then(() => {
      alert('Link copiado! Cole no seu Instagram Stories');
    });
    
    // Tentar abrir Instagram
    window.open(instagramUrl, '_blank');
    
    setTimeout(() => {
      window.open(webUrl, '_blank');
    }, 1000);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  if (error && !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">😔</div>
          <h1 className="text-2xl font-bold text-white mb-2">{error}</h1>
          <button 
            onClick={() => navigate('/')}
            className="text-yellow-400 hover:text-yellow-300 underline"
          >
            Voltar ao início
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <div className="bg-black/50 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                {user?.avatar_url ? (
                  <img 
                    src={user.avatar_url} 
                    alt={user.display_name}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <span className="text-black font-bold text-xl">
                    {user?.display_name?.charAt(0)?.toUpperCase()}
                  </span>
                )}
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">{user?.display_name}</h1>
                <p className="text-gray-400">@{user?.slug}</p>
                {user?.bio && (
                  <p className="text-gray-300 mt-1 max-w-md">{user.bio}</p>
                )}
              </div>
            </div>
            
            <button
              onClick={handleShareInstagram}
              className="flex items-center space-x-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all"
            >
              <Instagram className="w-5 h-5" />
              <span>Compartilhar</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid md:grid-cols-3 gap-8">
          {/* Formulário de Mensagem */}
          <div className="md:col-span-2">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <div className="flex items-center space-x-3 mb-6">
                <div className="w-12 h-12 bg-yellow-400 rounded-full flex items-center justify-center">
                  <MessageCircle className="w-6 h-6 text-black" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Envie uma mensagem anônima</h2>
                  <p className="text-gray-400">Sua identidade será mantida em segredo</p>
                </div>
              </div>

              {showSuccess && (
                <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4 mb-6">
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-xs">✓</span>
                    </div>
                    <span className="text-green-400 font-medium">Mensagem enviada com sucesso!</span>
                  </div>
                </div>
              )}

              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
                  <span className="text-red-400">{error}</span>
                </div>
              )}

              <form onSubmit={handleSendMessage}>
                <div className="mb-4">
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="Digite sua mensagem anônima aqui..."
                    className="w-full h-32 bg-gray-900/50 border border-gray-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-yellow-400 focus:ring-1 focus:ring-yellow-400 resize-none"
                    maxLength={5000}
                  />
                  <div className="flex justify-between items-center mt-2">
                    <span className="text-gray-500 text-sm">
                      {message.length}/5000 caracteres
                    </span>
                    <div className="flex items-center space-x-2 text-gray-400 text-sm">
                      <Shield className="w-4 h-4" />
                      <span>100% anônimo</span>
                    </div>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSending || !message.trim()}
                  className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-3 px-6 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isSending ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></div>
                      <span>Enviando...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-5 h-5" />
                      <span>Enviar Mensagem</span>
                    </>
                  )}
                </button>
              </form>

              <div className="mt-6 p-4 bg-gray-900/30 rounded-lg">
                <h3 className="text-white font-medium mb-2">Como funciona?</h3>
                <ul className="text-gray-400 text-sm space-y-1">
                  <li>• Sua mensagem é completamente anônima</li>
                  <li>• Não coletamos informações pessoais</li>
                  <li>• Mensagens são moderadas automaticamente</li>
                  <li>• Seja respeitoso e gentil</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Sidebar com Estatísticas */}
          <div className="space-y-6">
            {/* Estatísticas */}
            {stats && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h3 className="text-lg font-bold text-white mb-4">Estatísticas</h3>
                
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Mensagens recebidas</span>
                    <span className="text-white font-bold">{stats.approved_messages}</span>
                  </div>
                  
                  {stats.top_locations && stats.top_locations.length > 0 && (
                    <div>
                      <span className="text-gray-400 text-sm">Top localizações</span>
                      <div className="mt-2 space-y-2">
                        {stats.top_locations.slice(0, 3).map((location, index) => (
                          <div key={index} className="flex items-center space-x-2">
                            <MapPin className="w-4 h-4 text-yellow-400" />
                            <span className="text-white text-sm">
                              {location.city}, {location.region}
                            </span>
                            <span className="text-gray-400 text-sm">({location.count})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Call to Action */}
            <div className="bg-gradient-to-br from-yellow-400/20 to-orange-500/20 backdrop-blur-sm rounded-2xl p-6 border border-yellow-400/30">
              <div className="text-center">
                <Heart className="w-8 h-8 text-yellow-400 mx-auto mb-3" />
                <h3 className="text-lg font-bold text-white mb-2">Crie sua própria página</h3>
                <p className="text-gray-300 text-sm mb-4">
                  Receba mensagens anônimas dos seus seguidores
                </p>
                <button
                  onClick={() => navigate('/signup')}
                  className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-2 px-4 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all"
                >
                  Criar Conta Grátis
                </button>
              </div>
            </div>

            {/* Instagram Link */}
            {user?.instagram_username && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="text-center">
                  <Instagram className="w-8 h-8 text-pink-400 mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-white mb-2">Instagram</h3>
                  <a
                    href={`https://instagram.com/${user.instagram_username.replace('@', '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-pink-400 hover:text-pink-300 font-medium"
                  >
                    {user.instagram_username}
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-black/50 backdrop-blur-sm border-t border-gray-800 mt-16">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-yellow-400 rounded-full flex items-center justify-center">
                <span className="text-black font-bold text-sm">A</span>
              </div>
              <span className="text-white font-bold text-xl">ANONYMOUS</span>
            </div>
            <p className="text-gray-400 text-sm">
              Mensagens 100% anônimas e seguras
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PublicPage;
