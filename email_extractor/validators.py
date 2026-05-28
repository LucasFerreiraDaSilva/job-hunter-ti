"""
Validadores de email
Verifica formato, domínio e confiabilidade
"""

import re
import logging
from typing import Tuple

from config.settings import EMAIL_PATTERN, PRIORITY_KEYWORDS, IGNORE_KEYWORDS

logger = logging.getLogger(__name__)


class EmailValidator:
    """Validador e classificador de emails"""

    @staticmethod
    def validar_formato(email: str) -> bool:
        """
        Valida formato do email usando regex
        
        Args:
            email: Email para validar
            
        Returns:
            True se formato válido
        """
        try:
            if not email or not isinstance(email, str):
                return False
            
            email = email.strip().lower()
            
            # Validar com regex robusto
            if re.match(EMAIL_PATTERN, email):
                # Verificações adicionais
                if email.startswith(".") or email.endswith("."):
                    return False
                if ".." in email:
                    return False
                if "@" not in email:
                    return False
                
                local, dominio = email.rsplit("@", 1)
                
                # Local part não pode estar vazio
                if not local or len(local) > 64:
                    return False
                
                # Domínio deve ter pelo menos um ponto
                if "." not in dominio:
                    return False
                
                return True
        except Exception as e:
            logger.debug(f"Erro ao validar formato: {e}")
        
        return False

    @staticmethod
    def validar_dominio(email: str) -> bool:
        """
        Valida domínio do email
        
        Args:
            email: Email para validar
            
        Returns:
            True se domínio válido
        """
        try:
            if "@" not in email:
                return False
            
            dominio = email.split("@")[1].lower()
            
            # Verificações básicas de domínio
            if not dominio or dominio.startswith(".") or dominio.endswith("."):
                return False
            
            # Deve ter TLD válido
            partes = dominio.split(".")
            if len(partes) < 2:
                return False
            
            tld = partes[-1]
            if len(tld) < 2 or len(tld) > 6:
                return False
            
            # TLD deve ser apenas letras
            if not tld.isalpha():
                return False
            
            # Não permitir domínios muito comuns suspeitos
            dominios_suspeitos = [
                "test.com",
                "example.com",
                "localhost",
                "example.org",
                "test.org"
            ]
            
            if dominio in dominios_suspeitos:
                return False
            
            return True
        except Exception as e:
            logger.debug(f"Erro ao validar domínio: {e}")
        
        return False

    @staticmethod
    def verificar_ignore(email: str) -> bool:
        """
        Verifica se email deve ser ignorado
        
        Args:
            email: Email para verificar
            
        Returns:
            True se deve ser ignorado
        """
        email_lower = email.lower()
        
        for keyword in IGNORE_KEYWORDS:
            if keyword in email_lower:
                return True
        
        return False

    @staticmethod
    def calcular_confianca(email: str) -> float:
        """
        Calcula score de confiança do email (0-1)
        
        Args:
            email: Email para calcular
            
        Returns:
            Score de confiança (0-1)
        """
        score = 0.5  # Score base
        email_lower = email.lower()
        
        # Verificar se é prioritário
        for keyword in PRIORITY_KEYWORDS:
            if keyword in email_lower:
                score += 0.3
                break
        
        # Penalidades
        if email_lower.startswith(".") or email_lower.endswith("."):
            score -= 0.2
        
        if ".." in email_lower:
            score -= 0.2
        
        # Domínios conhecidos são mais confiáveis
        dominios_confiavel = [
            ".com.br",
            ".gov.br",
            ".edu.br",
            ".com",
            ".org",
            ".net",
            ".biz"
        ]
        
        for dominio in dominios_confiavel:
            if email_lower.endswith(dominio):
                score += 0.1
                break
        
        # Garantir range 0-1
        return min(max(score, 0.0), 1.0)

    @staticmethod
    def classificar_tipo(email: str) -> str:
        """
        Classifica tipo de email
        
        Args:
            email: Email para classificar
            
        Returns:
            Tipo de email
        """
        email_lower = email.lower()
        
        tipos = {
            "rh": ["rh@", "recrutamento@", "recursos.humanos@", "hr@"],
            "vagas": ["vagas@", "jobs@", "career@", "careers@"],
            "contato": ["contato@", "contact@", "info@", "hello@"],
            "comercial": ["comercial@", "sales@", "vendas@", "business@"],
            "trabalheconosco": ["trabalheconosco@", "join@", "hiring@"],
        }
        
        for tipo, keywords in tipos.items():
            for keyword in keywords:
                if keyword in email_lower:
                    return tipo
        
        return "geral"

    @staticmethod
    def validar_completo(email: str) -> Tuple[bool, float, str]:
        """
        Validação completa do email
        
        Args:
            email: Email para validar
            
        Returns:
            Tuple: (é_válido, confiança, tipo)
        """
        email = email.strip().lower()
        
        # Verificações básicas
        if not EmailValidator.validar_formato(email):
            return False, 0.0, "inválido"
        
        if not EmailValidator.validar_dominio(email):
            return False, 0.0, "inválido"
        
        if EmailValidator.verificar_ignore(email):
            return False, 0.0, "ignorado"
        
        confianca = EmailValidator.calcular_confianca(email)
        tipo = EmailValidator.classificar_tipo(email)
        
        return True, confianca, tipo
