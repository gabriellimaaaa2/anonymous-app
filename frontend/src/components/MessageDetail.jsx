import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  MapPin, 
  Eye, 
  EyeOff,
  Clock, 
  Shield,
  Flag,
  Trash2,
  Copy,
  Share2,
  CheckCircle,
  AlertCircle,
  XCircle,
  Globe,
  Wifi,
  Calendar,
  CreditCard,
  Lock
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const MessageDetail = () => {
  const { messageId } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRevealing, setIsRevealing] = useState(false);
  const [showRevealModal, setShowRevealModal] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (messageId) {
      fetchMessageDetail();
    }
  }, [messageId]);

  const fetchMessageDetail = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/user/messages/${messageId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage(response.data.message);
    } catch (error) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      } else if (error.response?.status === 404) {
        setError('Mensagem não encontrada');
      } else {
        setError('Erro ao carregar mensagem');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevealLocation = async () => {
    if (!message.can_reveal) {
      return;
    }

    setIsRevealing(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE}/payments/reveal/${messageId}`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      // Atualizar mensagem com dados revelados
      setMessage(prev => ({
        ...prev,
        is_revealed: true,
        reveal_details: response.data.reveal_details
      }));

      setShowRevealModal(false);
    } catch (error) {
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Erro ao revelar localização');
      }
    } finally {
      setIsRevealing(false);
    }
  };

  const handleReportMessage = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API_BASE}/public/report-message`, {
        message_id: messageId,
        reason: 'Conteúdo inadequado'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('Mensagem reportada com sucesso');
    } catch (error) {
      console.error('Erro ao reportar mensagem:', error);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-5 h-5 text-green-400" />;
      case 'pending':
        return <Clock className="w-5 h-5 text-yellow-400" />;
      case 'flagged':
        return <AlertCircle className="w-5 h-5 text-orange-400" />;
      case 'blocked':
        return <XCircle className="w-5 h-5 text-red-400" />;
      default:
        return <Shield className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'approved': return 'Aprovada';
      case 'pending': return 'Pendente de Moderação';
      case 'flagged': return 'Sinalizada para Revisão';
      case 'blocked': return 'Bloqueada';
      default: return status;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">😔</div>
          <h1 className="text-2xl font-bold text-white mb-2">{error}</h1>
          <button 
            onClick={() => navigate('/inbox')}
            className="text-yellow-400 hover:text-yellow-300 underline"
          >
            Voltar à caixa de entrada
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900">
      {/* Header */}
      <div className="bg-black/50 backdrop-blur-sm border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/inbox')}
                className="p-2 text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
              <div>
                <h1 className="text-xl font-bold text-white">Detalhes da Mensagem</h1>
                <p className="text-gray-400 text-sm">
                  Recebida em {formatDate(message.created_at)}
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleReportMessage}
                className="p-2 text-gray-400 hover:text-orange-400 transition-colors"
                title="Reportar mensagem"
              >
                <Flag className="w-5 h-5" />
              </button>
              <button
                className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                title="Excluir mensagem"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Message Content */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              {/* Status */}
              <div className="flex items-center space-x-2 mb-6">
                {getStatusIcon(message.moderation_status)}
                <span className="font-medium text-white">
                  {getStatusText(message.moderation_status)}
                </span>
                {message.moderation_status === 'pending' && (
                  <span className="text-gray-400 text-sm">
                    - Aguardando revisão
                  </span>
                )}
              </div>

              {/* Message Text */}
              <div className="bg-gray-900/50 rounded-lg p-6 mb-6">
                <p className="text-white text-lg leading-relaxed whitespace-pre-wrap">
                  {message.text}
                </p>
              </div>

              {/* Audio Message */}
              {message.audio_url && (
                <div className="bg-gray-900/50 rounded-lg p-4 mb-6">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-yellow-400 rounded-full flex items-center justify-center">
                      <span className="text-black text-sm">🎵</span>
                    </div>
                    <div>
                      <p className="text-white font-medium">Mensagem de áudio</p>
                      <audio controls className="mt-2">
                        <source src={message.audio_url} type="audio/mpeg" />
                        Seu navegador não suporta áudio.
                      </audio>
                    </div>
                  </div>
                </div>
              )}

              {/* Message Metadata */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2 text-gray-400">
                  <Calendar className="w-4 h-4" />
                  <span>Recebida: {formatDate(message.created_at)}</span>
                </div>
                
                {message.reports_count > 0 && (
                  <div className="flex items-center space-x-2 text-orange-400">
                    <Flag className="w-4 h-4" />
                    <span>{message.reports_count} report(s)</span>
                  </div>
                )}

                {message.vpn_flag && (
                  <div className="flex items-center space-x-2 text-orange-400">
                    <Wifi className="w-4 h-4" />
                    <span>Enviado via VPN</span>
                  </div>
                )}

                <div className="flex items-center space-x-2 text-gray-400">
                  <Shield className="w-4 h-4" />
                  <span>ID: {message.id.substring(0, 8)}...</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Location Information */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                <MapPin className="w-5 h-5 text-yellow-400" />
                <span>Localização</span>
              </h3>

              {message.is_revealed ? (
                <div className="space-y-3">
                  <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-3">
                    <div className="flex items-center space-x-2 mb-2">
                      <Eye className="w-4 h-4 text-green-400" />
                      <span className="text-green-400 font-medium">Localização Revelada</span>
                    </div>
                    <div className="text-white">
                      <p className="font-medium">{message.reveal_details?.city}</p>
                      <p className="text-gray-300">{message.reveal_details?.region}</p>
                      <p className="text-gray-400 text-sm mt-1">
                        Confiança: {message.reveal_details?.confidence_score}%
                      </p>
                    </div>
                  </div>
                  
                  <p className="text-gray-400 text-xs">
                    Revelada em {formatDate(message.revealed_at)}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {message.geo_city ? (
                    <div className="text-gray-300">
                      <p className="font-medium">{message.geo_city}</p>
                      <p className="text-gray-400">{message.geo_region}, {message.geo_country}</p>
                      {message.confidence_score && (
                        <div className="mt-2">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            message.confidence_label === 'ALTA' 
                              ? 'bg-green-500/20 text-green-400'
                              : message.confidence_label === 'MÉDIA'
                              ? 'bg-yellow-500/20 text-yellow-400'
                              : 'bg-red-500/20 text-red-400'
                          }`}>
                            Confiança: {message.confidence_label}
                          </span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-gray-400">
                      <p>Localização não disponível</p>
                    </div>
                  )}

                  {message.can_reveal ? (
                    <button
                      onClick={() => setShowRevealModal(true)}
                      className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-2 px-4 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all flex items-center justify-center space-x-2"
                    >
                      <Eye className="w-4 h-4" />
                      <span>Revelar Localização Exata</span>
                    </button>
                  ) : (
                    <div className="bg-gray-700/50 rounded-lg p-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <Lock className="w-4 h-4 text-gray-400" />
                        <span className="text-gray-400 font-medium">Não Disponível</span>
                      </div>
                      <p className="text-gray-500 text-sm">
                        {message.reveal_message || 'Localização não pode ser revelada'}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Technical Details */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4 flex items-center space-x-2">
                <Globe className="w-5 h-5 text-blue-400" />
                <span>Detalhes Técnicos</span>
              </h3>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Confiança:</span>
                  <span className="text-white">{message.confidence_score || 'N/A'}%</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">País:</span>
                  <span className="text-white">{message.geo_country || 'Desconhecido'}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-gray-400">Região:</span>
                  <span className="text-white">{message.geo_region || 'Desconhecida'}</span>
                </div>

                {message.provider_confidence && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Confiança do Provedor:</span>
                    <span className="text-white">{message.provider_confidence}%</span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span className="text-gray-400">VPN Detectada:</span>
                  <span className={message.vpn_flag ? 'text-orange-400' : 'text-green-400'}>
                    {message.vpn_flag ? 'Sim' : 'Não'}
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
              <h3 className="text-lg font-bold text-white mb-4">Ações</h3>
              
              <div className="space-y-3">
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(message.text);
                    alert('Texto copiado!');
                  }}
                  className="w-full flex items-center space-x-2 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors text-white"
                >
                  <Copy className="w-4 h-4" />
                  <span>Copiar Texto</span>
                </button>

                <button
                  onClick={() => {
                    const shareData = {
                      title: 'Mensagem Anônima',
                      text: message.text,
                      url: window.location.href
                    };
                    if (navigator.share) {
                      navigator.share(shareData);
                    } else {
                      navigator.clipboard.writeText(shareData.text);
                      alert('Texto copiado para compartilhar!');
                    }
                  }}
                  className="w-full flex items-center space-x-2 p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors text-white"
                >
                  <Share2 className="w-4 h-4" />
                  <span>Compartilhar</span>
                </button>

                <button
                  onClick={handleReportMessage}
                  className="w-full flex items-center space-x-2 p-3 bg-red-500/20 rounded-lg hover:bg-red-500/30 transition-colors text-red-400 border border-red-500/30"
                >
                  <Flag className="w-4 h-4" />
                  <span>Reportar Mensagem</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reveal Modal */}
      {showRevealModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-2xl p-6 max-w-md w-full border border-gray-700">
            <h3 className="text-xl font-bold text-white mb-4">Revelar Localização Exata</h3>
            
            <div className="bg-yellow-400/20 border border-yellow-400/50 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2 mb-2">
                <CreditCard className="w-5 h-5 text-yellow-400" />
                <span className="text-yellow-400 font-medium">Custo: 1 Crédito</span>
              </div>
              <p className="text-gray-300 text-sm">
                Você receberá a localização mais precisa disponível para esta mensagem.
              </p>
            </div>

            <p className="text-gray-300 text-sm mb-6">
              Esta ação irá consumir 1 crédito de revelação e não pode ser desfeita. 
              Você receberá informações mais detalhadas sobre a localização do remetente.
            </p>

            <div className="flex space-x-3">
              <button
                onClick={() => setShowRevealModal(false)}
                className="flex-1 bg-gray-700 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleRevealLocation}
                disabled={isRevealing}
                className="flex-1 bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-2 px-4 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all disabled:opacity-50"
              >
                {isRevealing ? 'Revelando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MessageDetail;
