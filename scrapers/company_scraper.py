"""
Scraper de empresas
Busca e extrai informações de empresas usando web scraping e Google Search
"""

import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config.settings import SCRAPE_PAGES
from scrapers.utils import ScraperUtils

logger = logging.getLogger(__name__)


class CompanyScraper:
    """Scraper para extrair informações de empresas"""

    def __init__(self):
        """Inicializa o scraper"""
        self.session = ScraperUtils.criar_sessao_com_retries()
        self.utils = ScraperUtils()

    def buscar_empresas_google(
        self,
        palavra_chave: str,
        cidade: str = "",
        limite: int = 10
    ) -> List[Dict]:
        """
        Busca empresas no Google
        
        NOTA: Esta é uma implementação básica. Para scraping de Google em produção,
        considere usar a Google Custom Search API (com limite de requisições)
        
        Args:
            palavra_chave: Palavra-chave para buscar
            cidade: Cidade (opcional)
            limite: Número máximo de resultados
            
        Returns:
            Lista de dicts com informações de empresas
        """
        empresas = []
        
        # Montar query
        query = f"{palavra_chave} {cidade}".strip()
        
        logger.info(f"Buscando empresas: {query}")
        
        # URLs de busca (usando DuckDuckGo como alternativa mais simples)
        try:
            url = f"https://duckduckgo.com/?q={query}+site:.com.br+or+site:.com"
            
            response = self.utils.fazer_requisicao(url, self.session)
            if not response:
                logger.warning(f"Não foi possível fazer requisição para: {url}")
                return empresas
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # DuckDuckGo: buscar resultados
            resultados = soup.find_all("a", {"class": "result__url"})
            
            for idx, resultado in enumerate(resultados[:limite]):
                try:
                    titulo = resultado.get_text(strip=True)
                    link = resultado.get("href")
                    
                    if link and not link.startswith("http"):
                        link = f"https://{link}"
                    
                    if link and titulo:
                        empresas.append({
                            "nome": titulo.split("/")[0].strip(),
                            "site": link,
                            "fonte": "Google Search",
                            "cidade": cidade,
                            "telefone": None
                        })
                        
                        if len(empresas) >= limite:
                            break
                except Exception as e:
                    logger.debug(f"Erro ao processar resultado: {e}")
                    continue
            
            logger.info(f"Encontradas {len(empresas)} empresas para: {query}")
            
        except Exception as e:
            logger.error(f"Erro ao buscar no Google: {e}")
        
        return empresas

    def extrair_site_empresa(self, url_site: str) -> Dict:
        """
        Extrai informações detalhadas de um site de empresa
        
        Args:
            url_site: URL do site da empresa
            
        Returns:
            Dict com informações extraídas
        """
        informacoes = {
            "url": url_site,
            "titulo": None,
            "descricao": None,
            "tecnologias": [],
            "paginas_disponiveis": []
        }
        
        try:
            response = self.utils.fazer_requisicao(url_site, self.session)
            if not response:
                logger.warning(f"Não foi possível acessar: {url_site}")
                return informacoes
            
            soup = BeautifulSoup(response.text, "lxml")
            
            # Extrair título
            titulo = soup.find("title")
            if titulo:
                informacoes["titulo"] = titulo.get_text(strip=True)
            
            # Extrair descrição
            meta_desc = soup.find("meta", {"name": "description"})
            if meta_desc:
                informacoes["descricao"] = meta_desc.get("content", "")
            
            # Encontrar links internos (páginas de contato, sobre, etc)
            links = soup.find_all("a", href=True)
            paginas_potenciais = []
            
            for link in links:
                href = link.get("href", "").lower()
                if any(pagina in href for pagina in SCRAPE_PAGES):
                    paginas_potenciais.append(href)
            
            informacoes["paginas_disponiveis"] = list(set(paginas_potenciais))
            
            logger.info(f"Informações extraídas de: {url_site}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair site: {e}")
        
        return informacoes

    def buscar_paginas_contato(
        self,
        url_base: str
    ) -> List[str]:
        """
        Busca possíveis páginas de contato/sobre
        
        Args:
            url_base: URL base do site
            
        Returns:
            Lista de URLs para scraping
        """
        paginas = [url_base]  # Sempre incluir página inicial
        
        domain = urlparse(url_base).netloc
        
        # Tentar cada página da lista
        for pagina in SCRAPE_PAGES:
            url_completa = urljoin(url_base, pagina)
            
            # Verificar se URL é do mesmo domínio
            if urlparse(url_completa).netloc == domain:
                response = self.utils.fazer_requisicao(url_completa, self.session)
                if response and response.status_code == 200:
                    paginas.append(url_completa)
                    logger.debug(f"Página encontrada: {url_completa}")
        
        return paginas

    def extrair_informacoes_basicas(self, url: str) -> Dict:
        """
        Extrai informações básicas de um site
        
        Args:
            url: URL do site
            
        Returns:
            Dict com informações
        """
        informacoes = {
            "telefone": None,
            "email_generico": None,
            "endereco": None,
            "redes_sociais": {}
        }
        
        try:
            response = self.utils.fazer_requisicao(url, self.session)
            if not response:
                return informacoes
            
            soup = BeautifulSoup(response.text, "lxml")
            html_text = response.text.lower()
            
            # Buscar telefone (padrão simples)
            import re
            telefone_pattern = r"\(?\d{2}\)?\s?9?\d{4}-\d{4}"
            telefones = re.findall(telefone_pattern, html_text)
            if telefones:
                informacoes["telefone"] = telefones[0]
            
            # Buscar redes sociais
            redes = {
                "linkedin": r"linkedin\.com/company",
                "facebook": r"facebook\.com",
                "instagram": r"instagram\.com",
                "twitter": r"twitter\.com"
            }
            
            for rede, pattern in redes.items():
                if re.search(pattern, html_text):
                    links = soup.find_all("a", href=re.compile(pattern))
                    if links:
                        informacoes["redes_sociais"][rede] = links[0].get("href")
            
            logger.debug(f"Informações extraídas: {informacoes}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair informações: {e}")
        
        return informacoes

    def fechar(self):
        """Fecha sessão HTTP"""
        if self.session:
            self.session.close()
            logger.info("Sessão de scraper fechada")
