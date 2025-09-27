import React, { useState, useRef, useEffect } from 'react';
import { 
  Download, 
  Share2, 
  Instagram, 
  Copy,
  RefreshCw,
  Palette,
  Type,
  AlignCenter,
  AlignLeft,
  AlignRight,
  Bold,
  Italic,
  X
} from 'lucide-react';

const InstagramStory = ({ message, onClose, isOpen }) => {
  const canvasRef = useRef(null);
  const [storyImage, setStoryImage] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('link'); // 'link' ou 'responder'
  const [textSettings, setTextSettings] = useState({
    fontSize: 24,
    fontWeight: 'normal',
    textAlign: 'center',
    color: '#FFFFFF',
    position: { x: 50, y: 60 } // Porcentagem da posição
  });

  // Templates disponíveis
  const templates = {
    link: {
      name: 'Compartilhar Link',
      image: '/assets/LINK.jpg',
      description: 'Para compartilhar seu link nos stories'
    },
    responder: {
      name: 'Responder Mensagem',
      image: '/assets/RESPONDER.jpg', 
      description: 'Para quando receber uma mensagem'
    }
  };

  useEffect(() => {
    if (isOpen && message) {
      generateStory();
    }
  }, [isOpen, message, selectedTemplate, textSettings]);

  const generateStory = async () => {
    if (!message || !canvasRef.current) return;

    setIsGenerating(true);
    
    try {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');
      
      // Configurar canvas para story do Instagram (1080x1920)
      canvas.width = 1080;
      canvas.height = 1920;

      // Carregar imagem de fundo
      const backgroundImage = new Image();
      backgroundImage.crossOrigin = 'anonymous';
      
      await new Promise((resolve, reject) => {
        backgroundImage.onload = resolve;
        backgroundImage.onerror = reject;
        backgroundImage.src = templates[selectedTemplate].image;
      });

      // Desenhar fundo
      ctx.drawImage(backgroundImage, 0, 0, canvas.width, canvas.height);

      // Configurar texto
      const fontSize = Math.floor(canvas.width * (textSettings.fontSize / 100));
      ctx.font = `${textSettings.fontWeight} ${fontSize}px Arial, sans-serif`;
      ctx.fillStyle = textSettings.color;
      ctx.textAlign = textSettings.textAlign;

      // Calcular posição do texto
      const x = (textSettings.position.x / 100) * canvas.width;
      const y = (textSettings.position.y / 100) * canvas.height;

      // Preparar texto da mensagem
      let displayText = '';
      if (selectedTemplate === 'link') {
        displayText = `anonymous.app/${message.slug_owner || 'usuario'}`;
      } else {
        // Para template de resposta, mostrar parte da mensagem
        displayText = message.text.length > 100 
          ? message.text.substring(0, 100) + '...'
          : message.text;
      }

      // Desenhar texto com quebra de linha se necessário
      const maxWidth = canvas.width * 0.8;
      const lineHeight = fontSize * 1.2;
      
      if (selectedTemplate === 'link') {
        // Para link, texto simples centralizado
        ctx.fillText(displayText, x, y);
      } else {
        // Para resposta, texto com quebra de linha
        const words = displayText.split(' ');
        let line = '';
        let currentY = y;

        for (let n = 0; n < words.length; n++) {
          const testLine = line + words[n] + ' ';
          const metrics = ctx.measureText(testLine);
          const testWidth = metrics.width;
          
          if (testWidth > maxWidth && n > 0) {
            ctx.fillText(line, x, currentY);
            line = words[n] + ' ';
            currentY += lineHeight;
          } else {
            line = testLine;
          }
        }
        ctx.fillText(line, x, currentY);
      }

      // Adicionar elementos decorativos se necessário
      if (selectedTemplate === 'link') {
        // Adicionar ícone de link ou seta
        ctx.fillStyle = '#FFD700';
        ctx.font = `${fontSize * 0.8}px Arial`;
        ctx.fillText('👆 Toque aqui', x, y + lineHeight * 2);
      }

      // Converter canvas para imagem
      const dataURL = canvas.toDataURL('image/png', 0.9);
      setStoryImage(dataURL);

    } catch (error) {
      console.error('Erro ao gerar story:', error);
      alert('Erro ao gerar story. Tente novamente.');
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadStory = () => {
    if (!storyImage) return;

    const link = document.createElement('a');
    link.download = `anonymous-story-${Date.now()}.png`;
    link.href = storyImage;
    link.click();
  };

  const shareToInstagram = () => {
    if (!storyImage) return;

    // Tentar usar a API nativa de compartilhamento
    if (navigator.share) {
      // Converter dataURL para blob
      fetch(storyImage)
        .then(res => res.blob())
        .then(blob => {
          const file = new File([blob], 'anonymous-story.png', { type: 'image/png' });
          
          navigator.share({
            title: 'Anonymous Story',
            text: 'Compartilhe no seu Instagram Stories!',
            files: [file]
          });
        })
        .catch(err => {
          console.error('Erro ao compartilhar:', err);
          // Fallback: download da imagem
          downloadStory();
        });
    } else {
      // Fallback: abrir Instagram web ou download
      if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        // Mobile: tentar abrir app do Instagram
        window.open('instagram://story-camera', '_blank');
        setTimeout(() => {
          downloadStory();
        }, 1000);
      } else {
        // Desktop: download da imagem
        downloadStory();
      }
    }
  };

  const copyLink = () => {
    const link = `https://anonymous.app/${message.slug_owner || 'usuario'}`;
    navigator.clipboard.writeText(link);
    alert('Link copiado!');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div>
            <h2 className="text-xl font-bold text-white">Criar Story para Instagram</h2>
            <p className="text-gray-400 text-sm">Personalize e compartilhe sua mensagem</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex flex-col lg:flex-row">
          {/* Preview */}
          <div className="lg:w-1/2 p-6 bg-gray-800/50">
            <div className="text-center">
              <h3 className="text-lg font-bold text-white mb-4">Preview</h3>
              
              {/* Story Preview */}
              <div className="relative inline-block">
                <div className="w-48 h-80 bg-gray-700 rounded-2xl overflow-hidden shadow-2xl">
                  {storyImage ? (
                    <img 
                      src={storyImage} 
                      alt="Story Preview"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      {isGenerating ? (
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
                      ) : (
                        <span className="text-gray-400">Gerando preview...</span>
                      )}
                    </div>
                  )}
                </div>
                
                {/* Instagram UI Overlay */}
                <div className="absolute top-4 left-4 right-4 flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                    <span className="text-white text-sm font-medium">anonymous</span>
                  </div>
                  <div className="text-white text-xs">agora</div>
                </div>
              </div>

              {/* Canvas oculto para geração */}
              <canvas
                ref={canvasRef}
                style={{ display: 'none' }}
              />
            </div>
          </div>

          {/* Controls */}
          <div className="lg:w-1/2 p-6 space-y-6">
            {/* Template Selection */}
            <div>
              <h4 className="text-white font-medium mb-3">Escolher Template</h4>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(templates).map(([key, template]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedTemplate(key)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      selectedTemplate === key
                        ? 'border-yellow-400 bg-yellow-400/10'
                        : 'border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    <div className="text-white font-medium text-sm">{template.name}</div>
                    <div className="text-gray-400 text-xs">{template.description}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Text Settings */}
            <div>
              <h4 className="text-white font-medium mb-3">Configurações do Texto</h4>
              
              <div className="space-y-4">
                {/* Font Size */}
                <div>
                  <label className="text-gray-300 text-sm">Tamanho da Fonte</label>
                  <input
                    type="range"
                    min="16"
                    max="40"
                    value={textSettings.fontSize}
                    onChange={(e) => setTextSettings(prev => ({
                      ...prev,
                      fontSize: parseInt(e.target.value)
                    }))}
                    className="w-full mt-1"
                  />
                  <span className="text-gray-400 text-xs">{textSettings.fontSize}px</span>
                </div>

                {/* Text Color */}
                <div>
                  <label className="text-gray-300 text-sm">Cor do Texto</label>
                  <div className="flex items-center space-x-2 mt-1">
                    <input
                      type="color"
                      value={textSettings.color}
                      onChange={(e) => setTextSettings(prev => ({
                        ...prev,
                        color: e.target.value
                      }))}
                      className="w-8 h-8 rounded border border-gray-600"
                    />
                    <span className="text-gray-400 text-sm">{textSettings.color}</span>
                  </div>
                </div>

                {/* Text Alignment */}
                <div>
                  <label className="text-gray-300 text-sm">Alinhamento</label>
                  <div className="flex space-x-2 mt-1">
                    {[
                      { value: 'left', icon: AlignLeft },
                      { value: 'center', icon: AlignCenter },
                      { value: 'right', icon: AlignRight }
                    ].map(({ value, icon: Icon }) => (
                      <button
                        key={value}
                        onClick={() => setTextSettings(prev => ({
                          ...prev,
                          textAlign: value
                        }))}
                        className={`p-2 rounded border ${
                          textSettings.textAlign === value
                            ? 'border-yellow-400 bg-yellow-400/10'
                            : 'border-gray-600 hover:border-gray-500'
                        }`}
                      >
                        <Icon className="w-4 h-4 text-white" />
                      </button>
                    ))}
                  </div>
                </div>

                {/* Position */}
                <div>
                  <label className="text-gray-300 text-sm">Posição Vertical</label>
                  <input
                    type="range"
                    min="20"
                    max="80"
                    value={textSettings.position.y}
                    onChange={(e) => setTextSettings(prev => ({
                      ...prev,
                      position: { ...prev.position, y: parseInt(e.target.value) }
                    }))}
                    className="w-full mt-1"
                  />
                  <span className="text-gray-400 text-xs">{textSettings.position.y}%</span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="space-y-3">
              <button
                onClick={generateStory}
                disabled={isGenerating}
                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white font-bold py-3 px-6 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>Gerando...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-5 h-5" />
                    <span>Regenerar Story</span>
                  </>
                )}
              </button>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={downloadStory}
                  disabled={!storyImage}
                  className="bg-gray-700 text-white py-2 px-4 rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Download className="w-4 h-4" />
                  <span>Download</span>
                </button>

                <button
                  onClick={shareToInstagram}
                  disabled={!storyImage}
                  className="bg-gradient-to-r from-purple-500 to-pink-500 text-white py-2 px-4 rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 flex items-center justify-center space-x-2"
                >
                  <Instagram className="w-4 h-4" />
                  <span>Instagram</span>
                </button>
              </div>

              {selectedTemplate === 'link' && (
                <button
                  onClick={copyLink}
                  className="w-full bg-yellow-500 text-black font-medium py-2 px-4 rounded-lg hover:bg-yellow-400 transition-colors flex items-center justify-center space-x-2"
                >
                  <Copy className="w-4 h-4" />
                  <span>Copiar Link</span>
                </button>
              )}
            </div>

            {/* Instructions */}
            <div className="bg-blue-500/20 border border-blue-500/50 rounded-lg p-4">
              <h5 className="text-blue-400 font-medium mb-2">Como usar:</h5>
              <ol className="text-blue-300 text-sm space-y-1">
                <li>1. Personalize o texto e cores</li>
                <li>2. Clique em "Instagram" ou "Download"</li>
                <li>3. Publique no seu Stories</li>
                <li>4. Aguarde as mensagens chegarem!</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InstagramStory;
