"""
Configurações globais do Job Hunter TI
"""

import os
from pathlib import Path

# Diretórios
BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"
DB_DIR = BASE_DIR / "core"

# Criar diretórios se não existirem
LOGS_DIR.mkdir(exist_ok=True)
EXPORTS_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DB_DIR / "jobhunter.db"

# Web Scraping
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2  # segundos
CONCURRENT_REQUESTS = 3

# Email Sending
MAX_EMAILS_PER_HOUR = 30
EMAIL_DELAY_MIN = 60  # segundos
EMAIL_DELAY_MAX = 180  # segundos

# Regex patterns
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

# Email priorities (palavras-chave para classificação)
PRIORITY_KEYWORDS = [
    "rh@",
    "recrutamento@",
    "vagas@",
    "contato@",
    "trabalheconosco@",
    "comercial@",
    "recursos.humanos@",
    "career@",
    "jobs@"
]

# Emails para ignorar
IGNORE_KEYWORDS = [
    "no-reply",
    "noreply",
    "do-not-reply",
    "newsletter",
    "marketing",
    "suporte",
    "support",
    "technical",
    "info",
    "webmaster",
    "admin",
    "test@"
]

# Páginas para raspar
SCRAPE_PAGES = [
    "/",
    "/contato",
    "/contact",
    "/sobre",
    "/about",
    "/trabalheconosco",
    "/careers",
    "/jobs",
    "/footer",
    "/institucional"
]

# User Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]

# Logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"
