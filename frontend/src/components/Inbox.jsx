import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  Filter, 
  Search, 
  MapPin, 
  Eye, 
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  MoreVertical,
  Trash2,
  Flag,
  ArrowLeft,
  Calendar
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const Inbox = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filters, setFilters] = useState({
    status: 'all',
    search: '',
    sortBy: 'created_at',
    sortOrder: 'desc'
  });
  const [selectedMessages, setSelectedMessages] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchMessages();
  }, [currentPage, filters]);

  const fetchMessages = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      
      const params = new URLSearchParams({
        page: currentPage,
        per_page: 20,
        status: filters.status,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      });

      if (filters.search) {
        params.append('search', filters.search);
      }

      const response = await axios.get(`${API_BASE}/user/messages?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMessages(response.data.messages);
      setTotalPages(response.data.pagination.pages);
    } catch (error) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
      console.error('Erro ao carregar mensagens:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };

  const handleSelectMessage = (messageId) => {
    setSelectedMessages(prev => 
      prev.includes(messageId) 
        ? prev.filter(id => id !== messageId)
        : [...prev, messageId]
    );
  };

  const handleSelectAll = () => {
    if (selectedMessages.length === messages.length) {
      setSelectedMessages([]);
    } else {
      setSelectedMessages(messages.map(m => m.id));
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-400" />;
      case 'flagged':
        return <AlertCircle className="w-4 h-4 text-orange-400" />;
      case 'blocked':
        return <XCircle className="w-4 h-4 text-red-400" />;
      default:
        return <MessageCircle className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'approved': return 'Aprovada';
      case 'pending': return 'Pendente';
      case 'flagged': return 'Sinalizada';
      case 'blocked': return 'Bloqueada';
      default: return status;
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 1) return 'Hoje';
    if (diffDays === 2) return 'Ontem';
    if (diffDays <= 7) return `${diffDays} dias atrás`;
    
    return date.toLocaleDateString('pt-BR');
  };

  if (isLoading && messages.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <div className="bg-black/50 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-white">Caixa de Entrada</h1>
                <p className="text-gray-400">Gerencie suas mensagens recebidas</p>
              </div>
            </div>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center space-x-2 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
            >
              <Filter className="w-4 h-4" />
              <span>Filtros</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Status</label>
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
                >
                  <option value="all">Todas</option>
                  <option value="approved">Aprovadas</option>
                  <option value="pending">Pendentes</option>
                  <option value="flagged">Sinalizadas</option>
                  <option value="blocked">Bloqueadas</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Ordenar por</label>
                <select
                  value={filters.sortBy}
                  onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
                >
                  <option value="created_at">Data</option>
                  <option value="confidence_score">Confiança</option>
                  <option value="reveal_count">Revelações</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Ordem</label>
                <select
                  value={filters.sortOrder}
                  onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
                  className="w-full bg-gray-700 text-white px-3 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
                >
                  <option value="desc">Mais recente</option>
                  <option value="asc">Mais antigo</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Buscar</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    value={filters.search}
                    onChange={(e) => handleFilterChange('search', e.target.value)}
                    placeholder="Buscar mensagens..."
                    className="w-full bg-gray-700 text-white pl-10 pr-3 py-2 rounded-lg border border-gray-600 focus:outline-none focus:border-yellow-400"
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Messages List */}
        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl border border-gray-700">
          {/* List Header */}
          <div className="p-6 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <input
                  type="checkbox"
                  checked={selectedMessages.length === messages.length && messages.length > 0}
                  onChange={handleSelectAll}
                  className="w-4 h-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400"
                />
                <span className="text-white font-medium">
                  {selectedMessages.length > 0 
                    ? `${selectedMessages.length} selecionada(s)`
                    : `${messages.length} mensagem(ns)`
                  }
                </span>
              </div>

              {selectedMessages.length > 0 && (
                <div className="flex items-center space-x-2">
                  <button className="p-2 text-gray-400 hover:text-red-400 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <button className="p-2 text-gray-400 hover:text-orange-400 transition-colors">
                    <Flag className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Messages */}
          <div className="divide-y divide-gray-700">
            {messages.length > 0 ? (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`p-6 hover:bg-gray-700/30 transition-colors cursor-pointer ${
                    selectedMessages.includes(message.id) ? 'bg-yellow-400/10' : ''
                  }`}
                  onClick={() => navigate(`/messages/${message.id}`)}
                >
                  <div className="flex items-start space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedMessages.includes(message.id)}
                      onChange={(e) => {
                        e.stopPropagation();
                        handleSelectMessage(message.id);
                      }}
                      className="w-4 h-4 text-yellow-400 bg-gray-700 border-gray-600 rounded focus:ring-yellow-400 mt-1"
                    />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          {getStatusIcon(message.moderation_status)}
                          <span className="text-sm font-medium text-gray-300">
                            {getStatusText(message.moderation_status)}
                          </span>
                          {message.geo_city && (
                            <div className="flex items-center space-x-1 text-gray-400">
                              <MapPin className="w-3 h-3" />
                              <span className="text-xs">
                                {message.geo_city}, {message.geo_region}
                              </span>
                            </div>
                          )}
                          {message.confidence_score && (
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              message.confidence_label === 'ALTA' 
                                ? 'bg-green-500/20 text-green-400'
                                : message.confidence_label === 'MÉDIA'
                                ? 'bg-yellow-500/20 text-yellow-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}>
                              {message.confidence_label}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2 text-gray-400 text-sm">
                          <Calendar className="w-4 h-4" />
                          <span>{formatDate(message.created_at)}</span>
                        </div>
                      </div>

                      <p className="text-white text-sm leading-relaxed mb-3">
                        {message.text.length > 300 
                          ? `${message.text.substring(0, 300)}...` 
                          : message.text
                        }
                      </p>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4 text-xs text-gray-400">
                          {message.is_revealed && (
                            <div className="flex items-center space-x-1">
                              <Eye className="w-3 h-3" />
                              <span>Revelada</span>
                            </div>
                          )}
                          {message.reports_count > 0 && (
                            <div className="flex items-center space-x-1">
                              <Flag className="w-3 h-3" />
                              <span>{message.reports_count} report(s)</span>
                            </div>
                          )}
                          {message.vpn_flag && (
                            <span className="bg-orange-500/20 text-orange-400 px-2 py-1 rounded">
                              VPN
                            </span>
                          )}
                        </div>

                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            // Menu de ações
                          }}
                          className="p-1 text-gray-400 hover:text-white transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-12 text-center">
                <MessageCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-medium text-white mb-2">Nenhuma mensagem encontrada</h3>
                <p className="text-gray-400 mb-6">
                  {filters.status !== 'all' || filters.search 
                    ? 'Tente ajustar os filtros para ver mais mensagens.'
                    : 'Compartilhe seu link para começar a receber mensagens anônimas!'
                  }
                </p>
                {filters.status !== 'all' || filters.search ? (
                  <button
                    onClick={() => {
                      setFilters({ status: 'all', search: '', sortBy: 'created_at', sortOrder: 'desc' });
                      setCurrentPage(1);
                    }}
                    className="text-yellow-400 hover:text-yellow-300 font-medium"
                  >
                    Limpar filtros
                  </button>
                ) : (
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-2 px-6 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all"
                  >
                    Voltar ao Dashboard
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="p-6 border-t border-gray-700">
              <div className="flex items-center justify-between">
                <span className="text-gray-400 text-sm">
                  Página {currentPage} de {totalPages}
                </span>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Anterior
                  </button>
                  
                  <div className="flex items-center space-x-1">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      const page = i + 1;
                      return (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          className={`px-3 py-1 rounded ${
                            currentPage === page
                              ? 'bg-yellow-400 text-black'
                              : 'bg-gray-700 text-white hover:bg-gray-600'
                          }`}
                        >
                          {page}
                        </button>
                      );
                    })}
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Próxima
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Inbox;
