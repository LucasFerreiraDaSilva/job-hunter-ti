"""
Extrator de emails de websites
Extrai emails de páginas web com filtragem e validação
"""

import re
import logging
from typing import Set, List, Dict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from config.settings import EMAIL_PATTERN, SCRAPE_PAGES
from scrapers.utils import ScraperUtils
from email_extractor.validators import EmailValidator

logger = logging.getLogger(__name__)


class EmailExtractor:
    """Extrator de emails de websites"""

    def __init__(self):
        """Inicializa o extrator"""
        self.session = ScraperUtils.criar_sessao_com_retries()
        self.utils = ScraperUtils()
        self.validator = EmailValidator()

    def extrair_emails_da_pagina(
        self,
        url: str,
        pagina_nome: str = "geral"
    ) -> Dict[str, List[Dict]]:
        """
        Extrai emails de uma página específica
        
        Args:
            url: URL da página
            pagina_nome: Nome/tipo da página
            
        Returns:
            Dict com emails organizados por tipo
        """
        resultado = {
            "validos": [],
            "invalidos": [],
            "ignorados": [],
            "pagina_nome": pagina_nome,
            "url": url
        }
        
        try:
            response = self.utils.fazer_requisicao(url, self.session)
            if not response:
                logger.warning(f"Não foi possível acessar: {url}")
                return resultado
            
            # Extrair emails do HTML
            emails_encontrados = self._extrair_emails_html(response.text)
            
            # Validar e classificar cada email
            for email in emails_encontrados:
                email = email.strip().lower()
                
                is_valido, confianca, tipo = self.validator.validar_completo(email)
                
                email_info = {
                    "email": email,
                    "confianca": confianca,
                    "tipo": tipo,
                    "pagina": pagina_nome
                }
                
                if is_valido:
                    resultado["validos"].append(email_info)
                    logger.debug(f"Email válido encontrado: {email} (confiança: {confianca:.2f})")
                elif tipo == "ignorado":
                    resultado["ignorados"].append(email_info)
                    logger.debug(f"Email ignorado: {email}")
                else:
                    resultado["invalidos"].append(email_info)
                    logger.debug(f"Email inválido: {email}")
            
            logger.info(f"Página {pagina_nome}: {len(resultado['validos'])} emails válidos extraídos")
            
        except Exception as e:
            logger.error(f"Erro ao extrair emails de {url}: {e}")
        
        return resultado

    def _extrair_emails_html(self, html_content: str) -> Set[str]:
        """
        Extrai emails do conteúdo HTML
        
        Args:
            html_content: Conteúdo HTML
            
        Returns:
            Set de emails encontrados
        """
        emails = set()
        
        try:
            # Buscar padrões de email no texto
            matches = re.findall(EMAIL_PATTERN, html_content)
            emails.update(matches)
            
            # Buscar em atributos href (links mailto)
            mailto_pattern = r"mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
            mailto_matches = re.findall(mailto_pattern, html_content)
            emails.update(mailto_matches)
            
            logger.debug(f"Emails encontrados no HTML: {len(emails)}")
            
        except Exception as e:
            logger.error(f"Erro ao extrair emails do HTML: {e}")
        
        return emails

    def extrair_emails_do_site(
        self,
        url_base: str,
        paginas_customizadas: List[str] = None
    ) -> List[Dict]:
        """
        Extrai emails de múltiplas páginas de um site
        
        Args:
            url_base: URL base do site
            paginas_customizadas: Lista customizada de páginas para raspar
            
        Returns:
            Lista de emails com informações
        """
        todos_emails = []
        
        # Usar páginas customizadas ou padrão
        paginas_para_raspar = paginas_customizadas or SCRAPE_PAGES
        
        # Sempre incluir página inicial
        if url_base not in paginas_para_raspar:
            paginas_para_raspar = ["/"] + paginas_para_raspar
        
        domain = urlparse(url_base).netloc
        
        for idx, pagina in enumerate(paginas_para_raspar, 1):
            try:
                # Construir URL completa
                if pagina.startswith("/"):
                    url_completa = urljoin(url_base, pagina)
                elif pagina.startswith("http"):
                    url_completa = pagina
                else:
                    url_completa = urljoin(url_base, f"/{pagina}")
                
                # Verificar se é do mesmo domínio
                if urlparse(url_completa).netloc != domain:
                    logger.debug(f"URL descartada (domínio diferente): {url_completa}")
                    continue
                
                logger.info(f"Extraindo emails de: {url_completa}")
                
                # Extrair emails da página
                resultado = self.extrair_emails_da_pagina(url_completa, pagina)
                
                # Adicionar à lista
                todos_emails.extend(resultado["validos"])
                
            except Exception as e:
                logger.error(f"Erro ao processar página {pagina}: {e}")
                continue
        
        # Remover duplicatas mantendo o de maior confiança
        emails_unicos = {}
        for email_info in todos_emails:
            email = email_info["email"]
            if email not in emails_unicos or email_info["confianca"] > emails_unicos[email]["confianca"]:
                emails_unicos[email] = email_info
        
        resultado_final = list(emails_unicos.values())
        logger.info(f"Total de emails únicos encontrados: {len(resultado_final)}")
        
        return resultado_final

    def extrair_emails_por_tipo(
        self,
        emails: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Organiza emails por tipo
        
        Args:
            emails: Lista de emails
            
        Returns:
            Dict com emails organizados por tipo
        """
        por_tipo = {}
        
        for email_info in emails:
            tipo = email_info.get("tipo", "geral")
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(email_info)
        
        return por_tipo

    def obter_email_prioritario(
        self,
        emails: List[Dict]
    ) -> Dict:
        """
        Obtém o email mais prioritário da lista
        
        Args:
            emails: Lista de emails
            
        Returns:
            Email com maior confiança
        """
        if not emails:
            return None
        
        return max(emails, key=lambda x: x.get("confianca", 0))

    def fechar(self):
        """Fecha sessão HTTP"""
        if self.session:
            self.session.close()
            logger.info("Sessão do extrator fechada")
