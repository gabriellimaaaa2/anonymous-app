-- Configuração inicial do Supabase para o projeto ANONYMOUS
-- Este arquivo contém todas as migrações SQL necessárias

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabela de usuários
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
    pass_hash VARCHAR(255) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    dob DATE,
    profile_image_url TEXT,
    plan_type VARCHAR(20) DEFAULT 'free' CHECK (plan_type IN ('free', 'monthly24_99', 'premium')),
    plan_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    reveal_balance INTEGER DEFAULT 0,
    system_messages_enabled BOOLEAN DEFAULT FALSE,
    system_messages_frequency INTEGER DEFAULT 0 CHECK (system_messages_frequency BETWEEN 0 AND 5)
);

-- Tabela de mensagens
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug_owner VARCHAR(50) NOT NULL REFERENCES users(slug) ON DELETE CASCADE,
    text TEXT NOT NULL,
    audio_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    ip_hash VARCHAR(64) NOT NULL,
    geo_country VARCHAR(2),
    geo_region VARCHAR(100),
    geo_city VARCHAR(100),
    geo_lat FLOAT,
    geo_lon FLOAT,
    provider_confidence INTEGER DEFAULT 0,
    vpn_flag BOOLEAN DEFAULT FALSE,
    ua TEXT,
    accept_language VARCHAR(100),
    moderation_status VARCHAR(20) DEFAULT 'pending' CHECK (moderation_status IN ('pending', 'approved', 'blocked', 'flagged')),
    reports_count INTEGER DEFAULT 0,
    is_system_message BOOLEAN DEFAULT FALSE,
    system_template_id VARCHAR(50),
    is_locked BOOLEAN DEFAULT FALSE,
    locked_price_cents INTEGER DEFAULT 0,
    reveal_count INTEGER DEFAULT 0,
    last_reveal_at TIMESTAMPTZ,
    confidence_score INTEGER DEFAULT 0
);

-- Tabela de logs de revelação
CREATE TABLE reveal_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    payment_provider VARCHAR(20),
    payment_id VARCHAR(100),
    amount_cents INTEGER NOT NULL,
    city VARCHAR(100),
    region VARCHAR(100),
    confidence_score INTEGER,
    map_geojson JSONB,
    notes TEXT
);

-- Tabela de pagamentos
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('stripe', 'pix', 'pagar_me', 'gerencianet')),
    provider_payment_id VARCHAR(100),
    amount_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'BRL',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    metadata JSONB
);

-- Tabela de logs de auditoria do admin
CREATE TABLE admin_audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id UUID NOT NULL REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    target VARCHAR(100),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de IPs encriptados (acesso restrito)
CREATE TABLE ip_vault (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    ip_encrypted TEXT NOT NULL,
    salt VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de templates de mensagens do sistema
CREATE TABLE system_message_templates (
    id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(20) NOT NULL CHECK (category IN ('agradavel', 'convite')),
    text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de IPs banidos
CREATE TABLE banned_ips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ip_hash VARCHAR(64) NOT NULL UNIQUE,
    reason TEXT,
    banned_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_messages_slug_owner ON messages(slug_owner);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_messages_moderation_status ON messages(moderation_status);
CREATE INDEX idx_reveal_logs_message_id ON reveal_logs(message_id);
CREATE INDEX idx_reveal_logs_user_id ON reveal_logs(user_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_admin_audit_logs_admin_id ON admin_audit_logs(admin_id);
CREATE INDEX idx_admin_audit_logs_created_at ON admin_audit_logs(created_at DESC);

-- Inserir templates de mensagens do sistema
INSERT INTO system_message_templates (id, category, text) VALUES
('agradavel_1', 'agradavel', 'Você tem um sorriso lindo!'),
('agradavel_2', 'agradavel', 'Adorei sua vibe, continue assim!'),
('agradavel_3', 'agradavel', 'Sua energia é contagiante!'),
('agradavel_4', 'agradavel', 'Você ilumina o ambiente por onde passa!'),
('convite_1', 'convite', 'Gostaria de me aproximar mais de você, vamos tomar um sorvete?'),
('convite_2', 'convite', 'Quero sair com você hoje'),
('convite_3', 'convite', 'Que tal tomarmos um café juntos?'),
('convite_4', 'convite', 'Gostaria de te conhecer melhor, podemos conversar?');

-- Função para gerar slug único
CREATE OR REPLACE FUNCTION generate_unique_slug(base_name TEXT)
RETURNS TEXT AS $$
DECLARE
    new_slug TEXT;
    counter INTEGER := 0;
BEGIN
    -- Limpar e formatar o nome base
    base_name := LOWER(REGEXP_REPLACE(base_name, '[^a-zA-Z0-9]', '', 'g'));
    
    -- Tentar o slug base primeiro
    new_slug := base_name;
    
    -- Se já existe, adicionar números até encontrar um único
    WHILE EXISTS (SELECT 1 FROM users WHERE slug = new_slug) LOOP
        counter := counter + 1;
        new_slug := base_name || counter::TEXT;
    END LOOP;
    
    RETURN new_slug;
END;
$$ LANGUAGE plpgsql;

-- Função para calcular confiança da localização
CREATE OR REPLACE FUNCTION calculate_location_confidence(
    provider_conf INTEGER,
    timezone_match BOOLEAN,
    language_match BOOLEAN,
    history_score INTEGER,
    vpn_detected BOOLEAN
)
RETURNS INTEGER AS $$
DECLARE
    confidence INTEGER;
BEGIN
    confidence := (provider_conf * 0.5)::INTEGER;
    
    IF timezone_match THEN
        confidence := confidence + 15;
    END IF;
    
    IF language_match THEN
        confidence := confidence + 10;
    END IF;
    
    confidence := confidence + LEAST(15, history_score * 5);
    
    IF vpn_detected THEN
        confidence := confidence - 30;
    END IF;
    
    -- Garantir que está entre 0 e 100
    confidence := GREATEST(0, LEAST(100, confidence));
    
    RETURN confidence;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar confidence_score automaticamente
CREATE OR REPLACE FUNCTION update_message_confidence()
RETURNS TRIGGER AS $$
BEGIN
    NEW.confidence_score := calculate_location_confidence(
        NEW.provider_confidence,
        FALSE, -- timezone_match será calculado na aplicação
        FALSE, -- language_match será calculado na aplicação
        0,     -- history_score será calculado na aplicação
        NEW.vpn_flag
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_message_confidence
    BEFORE INSERT OR UPDATE ON messages
    FOR EACH ROW
    EXECUTE FUNCTION update_message_confidence();

-- RLS (Row Level Security) para segurança
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE reveal_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;

-- Políticas RLS básicas (serão refinadas conforme necessário)
CREATE POLICY "Users can view own data" ON users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Messages visible to owner" ON messages
    FOR ALL USING (slug_owner IN (SELECT slug FROM users WHERE id = auth.uid()));

CREATE POLICY "Reveal logs visible to user" ON reveal_logs
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "Payments visible to user" ON payments
    FOR ALL USING (user_id = auth.uid());
