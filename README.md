````markdown
# 🎯 Job Hunter TI

Sistema automatizado para busca de empresas de TI, extração de emails de contato e envio profissional de currículo.

## 📋 Objetivo

Automatizar a busca de empresas próximas da sua região, coletar emails corporativos válidos relacionados a RH/recrutamento e enviar currículo de forma controlada, profissional e segura.

## ✨ Funcionalidades

- ✅ Busca automatizada de empresas (Google, DuckDuckGo)
- ✅ Extração inteligente de emails de websites
- ✅ Validação robusta de emails (formato, domínio, tipos)
- ✅ Classificação por prioridade (RH, Recrutamento, Contato, etc)
- ✅ Banco de dados SQLite com histórico completo
- ✅ Envio controlado de emails (máx 30/hora)
- ✅ Sistema de logs detalhado (TXT e JSON)
- ✅ Anti-bloqueio (User-Agents aleatórios, delays, retries)
- ✅ Interface CLI intuitiva
- ✅ Preparado para futuras melhorias

## 🏗️ Arquitetura

```
job-hunter-ti/
├── config/                 # Configurações globais
│   ├── settings.py        # Variáveis de configuração
│   └── emails_config.py   # Template de configuração de emails
├── core/                  # Núcleo do sistema
│   └── database.py        # Gerenciador SQLite
├── scrapers/              # Coleta de dados
│   ├── company_scraper.py # Busca e scraping de empresas
│   └── utils.py          # Utilitários (User-Agent, retry, etc)
├── email_extractor/       # Extração de emails
│   ├── extractor.py      # Extrator de emails de websites
│   └── validators.py     # Validadores de emails
├── email_sender/          # Envio de emails
│   └── smtp_handler.py   # Handler SMTP com controle
├── logs/                 # Arquivos de log
├── exports/              # Exportações (CSV, JSON)
├── requirements.txt      # Dependências Python
└── main.py              # CLI Principal

```

## 📦 Dependências

```
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
pandas==2.1.3
yagmail==0.15.293
fake-useragent==1.4.0
lxml==4.9.3
python-dotenv==1.0.0
```

## 🚀 Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/LucasFerreiraDaSilva/job-hunter-ti.git
cd job-hunter-ti
```

### 2. Criar ambiente virtual

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar credenciais (opcional para envio real)

```bash
cp config/emails_config.py.example config/emails_config.py
# Editar config/emails_config.py com suas credenciais
```

## 🎮 Como Usar

### Executar a aplicação

```bash
python main.py
```

### Menu principal

```
╔══════════════════════════════════════════════════╗
║         🎯 JOB HUNTER TI - v1.0 🎯              ║
║  Automatizador de Busca e Envio de Currículo    ║
╚══════════════════════════════════════════════════╝

┌─ MENU PRINCIPAL ─────────────────────────────────┐
│ 1. Buscar empresas                               │
│ 2. Extrair emails de empresa                     │
│ 3. Visualizar empresas armazenadas               │
│ 4. Visualizar emails                             │
│ 5. Enviar currículo (simulado)                   │
│ 6. Ver estatísticas                              │
│ 7. Limpar base de dados                          │
│ 0. Sair                                          │
└──────────────────────────────────────────────────┘
```

## 📚 Módulos Detalhados

### 1. **Database** (`core/database.py`)

Gerencia toda interação com SQLite. Inclui:
- Tabelas: `empresas`, `emails`, `envios`, `logs`
- CRUD operations
- Verificação de duplicatas
- Estatísticas

**Uso:**
```python
from core.database import Database

db = Database()
empresa_id = db.adicionar_empresa("Google", "https://google.com", "São Paulo")
db.adicionar_email(empresa_id, "rh@google.com", "rh", 0.95)
```

### 2. **CompanyScraper** (`scrapers/company_scraper.py`)

Busca e extrai informações de empresas. Inclui:
- Busca no Google/DuckDuckGo
- Extração de informações básicas
- Busca de páginas de contato

**Uso:**
```python
from scrapers.company_scraper import CompanyScraper

scraper = CompanyScraper()
empresas = scraper.buscar_empresas_google("TI", "São Paulo", limite=10)
```

### 3. **EmailExtractor** (`email_extractor/extractor.py`)

Extrai emails de websites com validação. Inclui:
- Regex robusto para emails
- Busca em múltiplas páginas
- Remoção de duplicatas

**Uso:**
```python
from email_extractor.extractor import EmailExtractor

extractor = EmailExtractor()
emails = extractor.extrair_emails_do_site("https://empresa.com")
```

### 4. **EmailValidator** (`email_extractor/validators.py`)

Valida e classifica emails. Inclui:
- Validação de formato
- Validação de domínio
- Classificação por tipo
- Score de confiança

**Uso:**
```python
from email_extractor.validators import EmailValidator

validator = EmailValidator()
is_valid, confianca, tipo = validator.validar_completo("rh@empresa.com")
```

### 5. **SMTPHandler** (`email_sender/smtp_handler.py`)

Gerencia envio de emails com controle. Inclui:
- Limite de 30 emails/hora
- Retry automático
- Suporte Gmail e Outlook
- Modo simulado para testes

**Uso:**
```python
from email_sender.smtp_handler import SMTPHandler

smtp = SMTPHandler("seu_email@gmail.com", "sua_app_password")
if smtp.pode_enviar():
    resultado = smtp.enviar_email("destinatario@empresa.com", "Assunto", "Corpo")
```

## 🔐 Segurança

### Práticas Implementadas:

1. **Anti-bloqueio**
   - User-Agents aleatórios
   - Delays entre requisições
   - Retry automático com backoff
   - Tratamento de timeouts

2. **Rate Limiting**
   - Máximo 30 emails/hora
   - Delays aleatórios entre envios
   - Fila com priorização

3. **Validação**
   - Formato de email (regex robusto)
   - Validação de domínio
   - Verificação de emails suspeitos
   - Filtro de spam/newsletters

4. **Credenciais**
   - Arquivo `.env` para configs sensíveis
   - Template `.example` para referência
   - Não commit de credenciais

## 📊 Banco de Dados

### Tabela `empresas`
```sql
id INTEGER PRIMARY KEY
nome TEXT UNIQUE NOT NULL
site TEXT
telefone TEXT
cidade TEXT
estado TEXT
url_maps TEXT
data_criacao TIMESTAMP
data_atualizacao TIMESTAMP
```

### Tabela `emails`
```sql
id INTEGER PRIMARY KEY
empresa_id INTEGER (FK)
email TEXT
tipo TEXT (rh, vagas, contato, comercial)
confianca REAL (0-1)
pagina_origem TEXT
status TEXT (valido, invalido, ignorado)
data_criacao TIMESTAMP
```

### Tabela `envios`
```sql
id INTEGER PRIMARY KEY
empresa_id INTEGER (FK)
email_id INTEGER (FK)
status TEXT (pendente, enviado, erro)
data_envio TIMESTAMP
resposta TEXT
erros TEXT
tentativas INTEGER
data_criacao TIMESTAMP
```

### Tabela `logs`
```sql
id INTEGER PRIMARY KEY
tipo TEXT (INFO, ERROR, WARNING)
mensagem TEXT
detalhes JSON
data_criacao TIMESTAMP
```

## 🚦 Status

- ✅ v1.0 - Funcionalidades básicas
  - Busca de empresas
  - Extração de emails
  - Banco de dados
  - CLI
  - Modo simulado

- 🔄 Melhorias futuras
  - Painel web (Flask/FastAPI)
  - Integração LinkedIn
  - IA para personalização
  - Dashboard de análise
  - API REST
  - Multi-thread/Async
  - Docker

## 📝 Logs

Todos os eventos são registrados em:
- **Arquivo**: `logs/jobhunter.log`
- **Banco de dados**: Tabela `logs`
- **Console**: Saída em tempo real

## 🔍 Tipos de Email Reconhecidos

**Prioritários:**
- rh@, recrutamento@, vagas@
- contato@, trabalheconosco@, comercial@
- recursos.humanos@, career@, jobs@

**Ignorados:**
- no-reply, newsletter, marketing
- suporte, technical, test@

## 📧 Configurar Envio Real

### Gmail

1. Ativar "Verificação em 2 etapas"
2. Gerar "Senha de app" em: https://myaccount.google.com/apppasswords
3. Usar a senha gerada em `config/emails_config.py`

### Outlook/Hotmail

1. Usar email e senha normalmente
2. Ou gerar "Senha de app" similar
3. Usar em `config/emails_config.py`

## ⚠️ Considerações Éticas

Este sistema foi desenvolvido para:
- ✅ Envio profissional e respeitoso
- ✅ Limite de 30 emails/hora
- ✅ Evitar spam e bloqueios
- ✅ Privacidade e segurança

Não use para:
- ❌ Scraping agressivo
- ❌ Spam em massa
- ❌ Coleta ilegal
- ❌ Contato não solicitado

## 🤝 Contribuindo

Contribuições são bem-vindas! Para melhorias:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Distribuído sob a licença MIT. Veja `LICENSE` para mais informações.

## 👨‍💻 Autor

**Lucas Ferreira da Silva**
- GitHub: [@LucasFerreiraDaSilva](https://github.com/LucasFerreiraDaSilva)

## 📧 Contato

Para dúvidas, sugestões ou reporte de bugs:
- Abra uma issue no GitHub
- Entre em contato via email

## 🙏 Agradecimentos

- Beautiful Soup - Web scraping
- Requests - HTTP client
- YagMail - Envio de emails
- SQLite - Banco de dados

## 📚 Recursos

- [Beautiful Soup Docs](https://www.crummy.com/software/BeautifulSoup/)
- [Requests Docs](https://docs.python-requests.org/)
- [SQLite Docs](https://www.sqlite.org/docs.html)
- [Python Regex](https://docs.python.org/3/library/re.html)

---

**Feito com ❤️ para a comunidade de TI**
````
