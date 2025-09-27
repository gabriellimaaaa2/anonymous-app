import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  User, 
  Mail, 
  MessageSquare, 
  Eye, 
  TrendingUp,
  Settings,
  LogOut,
  Plus,
  Share2,
  Copy,
  ExternalLink,
  Calendar,
  MapPin,
  Clock,
  Zap,
  CreditCard,
  BarChart3,
  Users,
  Globe,
  Shield,
  Instagram
} from 'lucide-react';
import axios from 'axios';
import InstagramStory from './InstagramStory';

const API_BASE = 'http://localhost:5000/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({});
  const [recentMessages, setRecentMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showInstagramStory, setShowInstagramStory] = useState(false);e('overview');
  const [messageFilter, setMessageFilter] = useState('approved');

  useEffect(() => {
    fetchDashboard();
    fetchMessages();
  }, []);

  useEffect(() => {
    if (messageFilter) {
      fetchMessages();
    }
  }, [messageFilter]);

  const fetchDashboard = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/user/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDashboard(response.data.dashboard);
    } catch (error) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/user/messages?status=${messageFilter}&per_page=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Erro ao carregar mensagens:', error);
    }
  };

  const handleCopyLink = () => {
    const link = `${window.location.origin}/${dashboard?.user?.slug}`;
    navigator.clipboard.writeText(link).then(() => {
      alert('Link copiado para a área de transferência!');
    });
  };

  const handleShareInstagram = () => {
    const link = `${window.location.origin}/${dashboard?.user?.slug}`;
    navigator.clipboard.writeText(link).then(() => {
      alert('Link copiado! Cole no seu Instagram Stories');
    });
    window.open('https://www.instagram.com/', '_blank');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  const dashboardStats = dashboard?.stats || {};
  const user = dashboard?.user || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <div className="bg-black/50 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                <span className="text-black font-bold text-lg">A</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">ANONYMOUS</h1>
                <p className="text-gray-400 text-sm">Dashboard</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/settings')}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                <Settings className="w-5 h-5" />
              </button>
              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-400 transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Profile Section */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 mb-8">
          <div className="flex flex-col md:flex-row md:items-center justify-between">
            <div className="flex items-center space-x-4 mb-4 md:mb-0">
              <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                {user.avatar_url ? (
                  <img 
                    src={user.avatar_url} 
                    alt={user.display_name}
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  <span className="text-black font-bold text-xl">
                    {user.display_name?.charAt(0)?.toUpperCase()}
                  </span>
                )}
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">{user.display_name}</h2>
                <p className="text-gray-400">@{user.slug}</p>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-yellow-400 text-sm">
                    {window.location.origin}/{user.slug}
                  </span>
                  <button
                    onClick={handleCopyLink}
                    className="p-1 text-gray-400 hover:text-yellow-400 transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => window.open(`${window.location.origin}/${user.slug}`, '_blank')}
                    className="p-1 text-gray-400 hover:text-yellow-400 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-3">
              <button
                onClick={handleCopyLink}
                className="flex items-center space-x-2 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
              >
                <Copy className="w-4 h-4" />
                <span>Copiar Link</span>
              </button>
              <button
                onClick={handleShareInstagram}
                className="flex items-center space-x-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-4 py-2 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all"
              >
                <Instagram className="w-4 h-4" />
                <span>Compartilhar</span>
              </button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total de Mensagens</p>
                <p className="text-2xl font-bold text-white">{dashboardStats.total_messages || 0}</p>
              </div>
              <MessageCircle className="w-8 h-8 text-yellow-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Aprovadas</p>
                <p className="text-2xl font-bold text-green-400">{dashboardStats.approved_messages || 0}</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Esta Semana</p>
                <p className="text-2xl font-bold text-blue-400">{dashboardStats.recent_messages || 0}</p>
              </div>
              <Calendar className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Revelações</p>
                <p className="text-2xl font-bold text-purple-400">{dashboardStats.total_reveals || 0}</p>
              </div>
              <Eye className="w-8 h-8 text-purple-400" />
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Messages List */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-white">Mensagens Recentes</h3>
                <select
                  value={messageFilter}
                  onChange={(e) => setMessageFilter(e.target.value)}
                  className="bg-gray-700 text-white px-3 py-1 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
                >
                  <option value="approved">Aprovadas</option>
                  <option value="pending">Pendentes</option>
                  <option value="all">Todas</option>
                </select>
              </div>

              <div className="space-y-4">
                {messages.length > 0 ? (
                  messages.map((message) => (
                    <div key={message.id} className="bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            message.moderation_status === 'approved' 
                              ? 'bg-green-500/20 text-green-400' 
                              : message.moderation_status === 'pending'
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            {message.moderation_status === 'approved' ? 'Aprovada' : 
                             message.moderation_status === 'pending' ? 'Pendente' : 'Bloqueada'}
                          </span>
                          {message.geo_city && (
                            <div className="flex items-center space-x-1 text-gray-400 text-xs">
                              <MapPin className="w-3 h-3" />
                              <span>{message.geo_city}, {message.geo_region}</span>
                            </div>
                          )}
                        </div>
                        <span className="text-gray-400 text-xs">
                          {new Date(message.created_at).toLocaleDateString('pt-BR')}
                        </span>
                      </div>
                      <p className="text-white text-sm leading-relaxed">
                        {message.text.length > 200 
                          ? `${message.text.substring(0, 200)}...` 
                          : message.text
                        }
                      </p>
                      {message.confidence_score && (
                        <div className="mt-2 flex items-center space-x-2">
                          <span className="text-gray-400 text-xs">Confiança da localização:</span>
                          <span className={`text-xs font-medium ${
                            message.confidence_label === 'ALTA' ? 'text-green-400' :
                            message.confidence_label === 'MÉDIA' ? 'text-yellow-400' : 'text-red-400'
                          }`}>
                            {message.confidence_label}
                          </span>
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <MessageCircle className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">Nenhuma mensagem encontrada</p>
                    <p className="text-gray-500 text-sm mt-1">
                      Compartilhe seu link para começar a receber mensagens!
                    </p>
                  </div>
                )}
              </div>

              {messages.length > 0 && (
                <div className="mt-6 text-center">
                  <button
                    onClick={() => navigate('/messages')}
                    className="text-yellow-400 hover:text-yellow-300 font-medium"
                  >
                    Ver todas as mensagens →
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Top Locations */}
            {dashboard?.top_locations && dashboard.top_locations.length > 0 && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h3 className="text-lg font-bold text-white mb-4">Top Localizações</h3>
                <div className="space-y-3">
                  {dashboard.top_locations.map((location, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <MapPin className="w-4 h-4 text-yellow-400" />
                        <span className="text-white text-sm">
                          {location.city}, {location.region}
                        </span>
                      </div>
                      <span className="text-gray-400 text-sm">{location.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4">Ações Rápidas</h3>
              <div className="space-y-3">
                <button
                  onClick={() => navigate('/profile')}
                  className="w-full text-left p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors text-white"
                >
                  Editar Perfil
                </button>
                <button
                  onClick={() => navigate('/settings')}
                  className="w-full text-left p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors text-white"
                >
                  Configurações
                </button>
                <button
                  onClick={handleShareInstagram}
                  className="w-full text-left p-3 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-lg hover:from-purple-500/30 hover:to-pink-500/30 transition-colors text-white border border-purple-500/30"
                >
                  Compartilhar no Instagram
                </button>
              </div>
            </div>

            {/* Credits */}
            <div className="bg-gradient-to-br from-yellow-400/20 to-orange-500/20 backdrop-blur-sm rounded-2xl p-6 border border-yellow-400/30">
              <h3 className="text-lg font-bold text-white mb-2">Créditos de Revelação</h3>
              <p className="text-3xl font-bold text-yellow-400 mb-2">{dashboardStats.reveal_credits || 0}</p>
              <p className="text-gray-300 text-sm mb-4">
                Use para descobrir a localização de quem enviou as mensagens
              </p>
              <button 
                onClick={() => navigate('/buy-credits')}
                className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-2 px-4 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all"
              >
                Comprar Mais Créditos
              </button>
            </div>

            {/* Instagram Story Button */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
              <div className="flex items-center space-x-3 mb-4">
                <Instagram className="w-6 h-6 text-pink-400" />
                <div>
                  <h3 className="text-lg font-bold text-white">Instagram Stories</h3>
                  <p className="text-gray-400 text-sm">Compartilhe e ganhe mais mensagens</p>
                </div>
              </div>
              <button 
                onClick={() => setShowInstagramStory(true)}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold py-2 px-4 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all flex items-center justify-center space-x-2"
              >
                <Instagram className="w-4 h-4" />
                <span>Criar Story</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Instagram Story Modal */}
      <InstagramStory
        message={{
          slug_owner: user?.slug || 'usuario',
          text: 'Mande uma mensagem anônima para mim!'
        }}
        isOpen={showInstagramStory}
        onClose={() => setShowInstagramStory(false)}
      />
    </div>
  );
};

export default Dashboard;
