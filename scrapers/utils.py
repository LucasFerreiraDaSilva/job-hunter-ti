"""
Utilitários para web scraping
Inclui tratamento de User-Agents, delays, retries e mais
"""

import time
import random
import logging
from typing import Optional
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from config.settings import (
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    DELAY_BETWEEN_REQUESTS,
    USER_AGENTS
)

logger = logging.getLogger(__name__)


class ScraperUtils:
    """Classe com utilitários para web scraping"""

    @staticmethod
    def obter_user_agent() -> str:
        """
        Retorna um User-Agent aleatório
        
        Returns:
            String com User-Agent
        """
        try:
            ua = UserAgent()
            return ua.random
        except Exception:
            # Fallback para lista pré-definida
            return random.choice(USER_AGENTS)

    @staticmethod
    def criar_sessao_com_retries() -> requests.Session:
        """
        Cria uma sessão requests com retry automático
        
        Returns:
            Session configurada
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    @staticmethod
    def fazer_requisicao(
        url: str,
        session: requests.Session = None,
        metodo: str = "GET",
        tentativa: int = 1
    ) -> Optional[requests.Response]:
        """
        Faz requisição HTTP com tratamento de erros
        
        Args:
            url: URL para fazer requisição
            session: Sessão requests (cria nova se None)
            metodo: Método HTTP (GET, POST, etc)
            tentativa: Número da tentativa (para logging)
            
        Returns:
            Response object ou None se falhar
        """
        if session is None:
            session = ScraperUtils.criar_sessao_com_retries()
        
        headers = {
            "User-Agent": ScraperUtils.obter_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # Delay aleatório para não ser agressivo
            delay = random.uniform(DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_REQUESTS + 2)
            time.sleep(delay)
            
            logger.info(f"Requisição {tentativa}: {url}")
            
            response = session.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            response.raise_for_status()
            
            logger.info(f"Sucesso: {url} (Status: {response.status_code})")
            return response
            
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout na requisição: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Erro de conexão: {url}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"Erro HTTP {e.response.status_code}: {url}")
            return None
        except Exception as e:
            logger.error(f"Erro ao fazer requisição: {e}")
            return None

    @staticmethod
    def parsear_html(html_content: str) -> Optional[BeautifulSoup]:
        """
        Parseia HTML com BeautifulSoup
        
        Args:
            html_content: Conteúdo HTML
            
        Returns:
            BeautifulSoup object ou None
        """
        try:
            return BeautifulSoup(html_content, "lxml")
        except Exception as e:
            logger.error(f"Erro ao parsear HTML: {e}")
            return None

    @staticmethod
    def extrair_texto(soup: BeautifulSoup, seletor: str = None) -> str:
        """
        Extrai texto do HTML parseado
        
        Args:
            soup: BeautifulSoup object
            seletor: Seletor CSS (opcional)
            
        Returns:
            Texto extraído
        """
        try:
            if seletor:
                elemento = soup.select_one(seletor)
                return elemento.get_text(strip=True) if elemento else ""
            return soup.get_text(strip=True)
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
            return ""

    @staticmethod
    def esperar_delay():
        """Espera delay aleatório entre requisições"""
        delay = random.uniform(DELAY_BETWEEN_REQUESTS, DELAY_BETWEEN_REQUESTS * 1.5)
        time.sleep(delay)
