# ANONYMOUS - Plataforma de Perguntas e Respostas Anônimas

Bem-vindo ao projeto ANONYMOUS, uma plataforma de perguntas e respostas anônimas inspirada no NGL, com foco em monetização e viralização através de funcionalidades de compartilhamento no Instagram. Este projeto é composto por um frontend React (PWA) e um backend Flask, utilizando Supabase como banco de dados e serviços de autenticação.

## Visão Geral do Projeto

O ANONYMOUS permite que usuários criem perfis, recebam perguntas anônimas e respondam a elas. A monetização ocorre através da compra de créditos para revelar a localização aproximada dos remetentes das mensagens. A viralização é impulsionada pela fácil integração com o Instagram Stories, permitindo que os usuários compartilhem suas caixas de perguntas e respostas de forma visualmente atraente.

### Funcionalidades Principais

-   **Autenticação Completa**: Cadastro, Login, Recuperação de Senha, Verificação de E-mail.
-   **Perfis Públicos**: Páginas personalizadas para receber mensagens anônimas.
-   **Envio de Mensagens Anônimas**: Usuários podem enviar mensagens de forma anônima para outros perfis.
-   **Caixa de Entrada (Inbox)**: Gerenciamento de mensagens recebidas, com filtros e detalhes.
-   **Monetização (Créditos)**: Compra de créditos via PIX (e futuramente Cartão de Crédito) para revelar a localização dos remetentes.
-   **GeoIP e Moderação**: Detecção de localização aproximada do remetente e sistema de moderação de conteúdo.
-   **Geração de Instagram Stories**: Ferramenta para criar imagens personalizadas para compartilhamento no Instagram, com base nas mensagens ou no link do perfil.
-   **Painel Administrativo**: Gerenciamento de usuários, mensagens, moderação, métricas e configurações do sistema.
-   **PWA (Progressive Web App)**: Experiência de usuário otimizada para dispositivos móveis.

## Estrutura do Projeto

O projeto está dividido em três diretórios principais:

-   `frontend/`: Aplicação React (PWA).
-   `backend/`: Aplicação Flask (API RESTful).
-   `infra/`: Scripts de configuração de infraestrutura (ex: Supabase).
-   `doc/`: Documentação adicional (ex: Swagger, Postman Collection).

```
anonymous-app/
├── frontend/             # Aplicação React
│   ├── public/
│   ├── src/
│   └── ...
├── backend/              # Aplicação Flask
│   ├── src/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   └── ...
├── infra/                # Scripts de infraestrutura (ex: Supabase SQL)
│   └── supabase_config.sql
├── doc/                  # Documentação (Swagger, Postman)
├── scripts/              # Scripts auxiliares (ex: create-zip.js)
├── .env.example          # Exemplo de variáveis de ambiente
├── package.json          # Gerenciamento de scripts do projeto
└── README.md             # Este arquivo
```

## Configuração do Ambiente

### Pré-requisitos

-   Node.js (v18 ou superior) e pnpm (para o frontend)
-   Python (v3.9 ou superior) e pip (para o backend)
-   Docker e Docker Compose (opcional, para rodar Supabase localmente)
-   Conta Supabase (para ambiente de produção)

### 1. Configurar Supabase

O projeto utiliza o Supabase para banco de dados e autenticação. Você pode configurá-lo localmente com Docker ou usar uma instância remota.

**Localmente (com Docker):**

```bash
# Certifique-se de ter Docker e Docker Compose instalados
cd infra
docker compose up -d
```

Após iniciar, aplique as migrações do `supabase_config.sql` através do painel do Supabase ou via CLI:

```bash
# Exemplo de aplicação via CLI (substitua com suas credenciais)
supabase login
supabase link --project-ref <your-project-ref>
supabase db diff --local > migrations/V1__initial_schema.sql
supabase migration up
```

**Remotamente (com instância Supabase):**

Crie um novo projeto no Supabase e configure as tabelas e funções SQL conforme o arquivo `infra/supabase_config.sql`.

### 2. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto (`anonymous-app/`) e preencha com as seguintes variáveis (baseado em `.env.example`):

```env
# Backend (Flask)
FLASK_APP=src.main
FLASK_ENV=development # ou production
SECRET_KEY=sua_chave_secreta_flask_aqui
JWT_SECRET_KEY=sua_chave_secreta_jwt_aqui

# Supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.your-project-ref.supabase.co:5432/postgres

# Email (para verificação e recuperação de senha)
MAIL_SERVER=smtp.seudominio.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@seudominio.com
MAIL_PASSWORD=sua_senha_email
MAIL_DEFAULT_SENDER=seu_email@seudominio.com

# GeoIP (MaxMind GeoLite2)
MAXMIND_LICENSE_KEY=your_maxmind_license_key # Necessário para baixar o banco de dados GeoLite2
GEOLITE2_DB_PATH=./data/GeoLite2-City.mmdb # Caminho para o arquivo .mmdb

# Pagamentos (Ex: Stripe, Mercado Pago, etc.)
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
WEBHOOK_SECRET=sua_chave_secreta_webhook

# Frontend
VITE_SUPABASE_URL=https://your-project-ref.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-public-key
VITE_API_BASE_URL=http://localhost:5000/api # ou URL do seu backend em produção
```

### 3. Instalar Dependências

**Backend (Python):**

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend (React):**

```bash
cd frontend
pnpm install
```

## Como Rodar a Aplicação

### Backend (Flask)

No diretório `backend/`:

```bash
source venv/bin/activate
flask run --host=0.0.0.0 --port=5000
```

O backend estará disponível em `http://localhost:5000`.

### Frontend (React)

No diretório `frontend/`:

```bash
pnpm run dev
```

O frontend estará disponível em `http://localhost:5173` (ou outra porta disponível).

## Testes

### Backend (Python)

No diretório `backend/`:

```bash
source venv/bin/activate
pytest
# Para ver cobertura de código
pytest --cov=src --cov-report=html
```

### Frontend (React)

No diretório `frontend/`:

```bash
pnpm test
```

## Documentação da API (Swagger/OpenAPI)

A documentação interativa da API estará disponível em `http://localhost:5000/swagger-ui` (ou `/docs`) quando o backend estiver rodando.

## Coleção Postman

Uma coleção Postman será gerada e incluída no diretório `doc/` para facilitar o teste manual da API.

## Scripts de Seed

Scripts para popular o banco de dados com dados de exemplo estarão disponíveis em `backend/scripts/seed.py`.

## Deploy

Instruções detalhadas para deploy em ambientes de produção (ex: Vercel para frontend, Render/Fly.io para backend) serão fornecidas separadamente ou podem ser configuradas com base nas suas preferências.

## Contribuição

Sinta-se à vontade para contribuir com melhorias, correções de bugs ou novas funcionalidades. Por favor, siga as diretrizes de contribuição (a serem definidas).

## Licença

Este projeto é licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

