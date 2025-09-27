import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  CreditCard, 
  Smartphone,
  Check,
  Star,
  Zap,
  Gift,
  Clock,
  Copy,
  QrCode,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

const BuyCredits = () => {
  const navigate = useNavigate();
  const [packages, setPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('pix');
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentData, setPaymentData] = useState(null);
  const [currentStep, setCurrentStep] = useState('select'); // select, payment, confirmation
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPackages();
  }, []);

  const fetchPackages = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/payments/packages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPackages(response.data.packages);
    } catch (error) {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        navigate('/login');
      }
      setError('Erro ao carregar pacotes');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePayment = async () => {
    if (!selectedPackage) return;

    setIsProcessing(true);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_BASE}/payments/create-payment`, {
        package_id: selectedPackage.id,
        payment_method: paymentMethod
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setPaymentData(response.data);
      setCurrentStep('payment');
    } catch (error) {
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Erro ao processar pagamento');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCopyPixCode = () => {
    if (paymentData?.payment_data?.pix_code) {
      navigator.clipboard.writeText(paymentData.payment_data.pix_code);
      alert('Código PIX copiado!');
    }
  };

  const checkPaymentStatus = async () => {
    if (!paymentData?.payment?.id) return;

    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/payments/payment-status/${paymentData.payment.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (response.data.payment.status === 'completed') {
        setCurrentStep('confirmation');
      }
    } catch (error) {
      console.error('Erro ao verificar status:', error);
    }
  };

  useEffect(() => {
    if (currentStep === 'payment' && paymentMethod === 'pix') {
      const interval = setInterval(checkPaymentStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [currentStep, paymentMethod]);

  if (isLoading) {
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
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => navigate('/dashboard')}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-white">Comprar Créditos</h1>
              <p className="text-gray-400">Revele a localização de quem enviou as mensagens</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {currentStep === 'select' && (
          <>
            {/* Package Selection */}
            <div className="mb-8">
              <h2 className="text-xl font-bold text-white mb-6">Escolha seu pacote</h2>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {packages.map((pkg) => (
                  <div
                    key={pkg.id}
                    onClick={() => setSelectedPackage(pkg)}
                    className={`relative bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border cursor-pointer transition-all hover:scale-105 ${
                      selectedPackage?.id === pkg.id
                        ? 'border-yellow-400 bg-yellow-400/10'
                        : 'border-gray-700 hover:border-gray-600'
                    } ${pkg.popular ? 'ring-2 ring-yellow-400/50' : ''}`}
                  >
                    {pkg.popular && (
                      <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                        <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black px-3 py-1 rounded-full text-xs font-bold flex items-center space-x-1">
                          <Star className="w-3 h-3" />
                          <span>POPULAR</span>
                        </div>
                      </div>
                    )}

                    <div className="text-center">
                      <div className="w-16 h-16 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Zap className="w-8 h-8 text-black" />
                      </div>
                      
                      <h3 className="text-lg font-bold text-white mb-2">{pkg.name}</h3>
                      <p className="text-gray-400 text-sm mb-4">{pkg.description}</p>
                      
                      <div className="mb-4">
                        <span className="text-2xl font-bold text-white">R$ {pkg.price_brl}</span>
                        <div className="text-gray-400 text-sm">
                          {pkg.credits} créditos
                          {pkg.bonus && (
                            <span className="text-green-400 ml-1">+ {pkg.bonus} bônus</span>
                          )}
                        </div>
                      </div>

                      {pkg.bonus && (
                        <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-2 mb-4">
                          <div className="flex items-center justify-center space-x-1 text-green-400 text-xs">
                            <Gift className="w-3 h-3" />
                            <span>{pkg.bonus} créditos extras grátis!</span>
                          </div>
                        </div>
                      )}

                      <div className="text-gray-400 text-xs">
                        R$ {(pkg.price_brl / (pkg.credits + (pkg.bonus || 0))).toFixed(2)} por crédito
                      </div>
                    </div>

                    {selectedPackage?.id === pkg.id && (
                      <div className="absolute top-4 right-4">
                        <div className="w-6 h-6 bg-yellow-400 rounded-full flex items-center justify-center">
                          <Check className="w-4 h-4 text-black" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Payment Method Selection */}
            {selectedPackage && (
              <div className="mb-8">
                <h2 className="text-xl font-bold text-white mb-6">Método de pagamento</h2>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div
                    onClick={() => setPaymentMethod('pix')}
                    className={`bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border cursor-pointer transition-all ${
                      paymentMethod === 'pix'
                        ? 'border-yellow-400 bg-yellow-400/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                        <Smartphone className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">PIX</h3>
                        <p className="text-gray-400 text-sm">Pagamento instantâneo</p>
                        <p className="text-green-400 text-xs">Aprovação imediata</p>
                      </div>
                      {paymentMethod === 'pix' && (
                        <div className="ml-auto">
                          <Check className="w-5 h-5 text-yellow-400" />
                        </div>
                      )}
                    </div>
                  </div>

                  <div
                    onClick={() => setPaymentMethod('credit_card')}
                    className={`bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border cursor-pointer transition-all ${
                      paymentMethod === 'credit_card'
                        ? 'border-yellow-400 bg-yellow-400/10'
                        : 'border-gray-700 hover:border-gray-600'
                    }`}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                        <CreditCard className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="text-lg font-bold text-white">Cartão de Crédito</h3>
                        <p className="text-gray-400 text-sm">Visa, Mastercard, Elo</p>
                        <p className="text-blue-400 text-xs">Parcelamento disponível</p>
                      </div>
                      {paymentMethod === 'credit_card' && (
                        <div className="ml-auto">
                          <Check className="w-5 h-5 text-yellow-400" />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Summary and Confirm */}
            {selectedPackage && (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h3 className="text-lg font-bold text-white mb-4">Resumo do pedido</h3>
                
                <div className="space-y-3 mb-6">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Pacote:</span>
                    <span className="text-white">{selectedPackage.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Créditos:</span>
                    <span className="text-white">
                      {selectedPackage.credits}
                      {selectedPackage.bonus && (
                        <span className="text-green-400"> + {selectedPackage.bonus} bônus</span>
                      )}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Método:</span>
                    <span className="text-white">
                      {paymentMethod === 'pix' ? 'PIX' : 'Cartão de Crédito'}
                    </span>
                  </div>
                  <div className="border-t border-gray-700 pt-3">
                    <div className="flex justify-between text-lg font-bold">
                      <span className="text-white">Total:</span>
                      <span className="text-yellow-400">R$ {selectedPackage.price_brl}</span>
                    </div>
                  </div>
                </div>

                {error && (
                  <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 mb-4">
                    <span className="text-red-400">{error}</span>
                  </div>
                )}

                <button
                  onClick={handleCreatePayment}
                  disabled={isProcessing}
                  className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-3 px-6 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
                >
                  {isProcessing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black"></div>
                      <span>Processando...</span>
                    </>
                  ) : (
                    <>
                      <span>Finalizar Compra</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </>
        )}

        {currentStep === 'payment' && paymentData && (
          <div className="max-w-2xl mx-auto">
            {paymentMethod === 'pix' ? (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <div className="text-center mb-6">
                  <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                    <QrCode className="w-8 h-8 text-white" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2">Pagamento PIX</h2>
                  <p className="text-gray-400">Escaneie o QR Code ou copie o código PIX</p>
                </div>

                {/* QR Code */}
                <div className="bg-white rounded-lg p-4 mb-6 text-center">
                  <img 
                    src={paymentData.payment_data.qr_code_url} 
                    alt="QR Code PIX"
                    className="mx-auto mb-4 w-48 h-48 bg-gray-200 rounded"
                  />
                  <p className="text-gray-600 text-sm">Escaneie com o app do seu banco</p>
                </div>

                {/* PIX Code */}
                <div className="bg-gray-900/50 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-400 text-sm">Código PIX:</span>
                    <button
                      onClick={handleCopyPixCode}
                      className="flex items-center space-x-1 text-yellow-400 hover:text-yellow-300 text-sm"
                    >
                      <Copy className="w-4 h-4" />
                      <span>Copiar</span>
                    </button>
                  </div>
                  <p className="text-white text-sm font-mono break-all">
                    {paymentData.payment_data.pix_code}
                  </p>
                </div>

                {/* Instructions */}
                <div className="mb-6">
                  <h3 className="text-white font-medium mb-3">Como pagar:</h3>
                  <ol className="space-y-2">
                    {paymentData.payment_data.instructions.map((instruction, index) => (
                      <li key={index} className="flex items-start space-x-2 text-gray-300 text-sm">
                        <span className="bg-yellow-400 text-black rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold mt-0.5">
                          {index + 1}
                        </span>
                        <span>{instruction}</span>
                      </li>
                    ))}
                  </ol>
                </div>

                {/* Timer */}
                <div className="bg-yellow-400/20 border border-yellow-400/50 rounded-lg p-4 mb-6">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-yellow-400" />
                    <span className="text-yellow-400 font-medium">
                      Este código expira em 30 minutos
                    </span>
                  </div>
                </div>

                {/* Status Check */}
                <div className="text-center">
                  <button
                    onClick={checkPaymentStatus}
                    className="flex items-center space-x-2 bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors mx-auto"
                  >
                    <RefreshCw className="w-4 h-4" />
                    <span>Verificar Pagamento</span>
                  </button>
                  <p className="text-gray-400 text-sm mt-2">
                    Verificamos automaticamente a cada 5 segundos
                  </p>
                </div>
              </div>
            ) : (
              <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-6 border border-gray-700">
                <h2 className="text-2xl font-bold text-white mb-6 text-center">Pagamento com Cartão</h2>
                <p className="text-gray-400 text-center">
                  Integração com Stripe em desenvolvimento...
                </p>
              </div>
            )}
          </div>
        )}

        {currentStep === 'confirmation' && (
          <div className="max-w-2xl mx-auto text-center">
            <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700">
              <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
                <Check className="w-10 h-10 text-white" />
              </div>
              
              <h2 className="text-3xl font-bold text-white mb-4">Pagamento Confirmado!</h2>
              <p className="text-gray-400 mb-6">
                Seus créditos foram adicionados à sua conta com sucesso.
              </p>
              
              <div className="bg-green-500/20 border border-green-500/50 rounded-lg p-4 mb-6">
                <p className="text-green-400 font-medium">
                  + {selectedPackage?.credits + (selectedPackage?.bonus || 0)} créditos adicionados
                </p>
              </div>
              
              <button
                onClick={() => navigate('/dashboard')}
                className="bg-gradient-to-r from-yellow-400 to-orange-500 text-black font-bold py-3 px-8 rounded-lg hover:from-yellow-500 hover:to-orange-600 transition-all"
              >
                Voltar ao Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BuyCredits;
