"""
Handler SMTP para envio de emails
Implementa envio controlado, fila de espera e retry
"""

import logging
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class SMTPHandler:
    """Handler para envio de emails via SMTP"""

    def __init__(
        self,
        sender_email: str,
        sender_password: str,
        sender_name: str = None,
        max_emails_per_hour: int = 30
    ):
        """
        Inicializa o handler SMTP
        
        Args:
            sender_email: Email do remetente
            sender_password: Senha/App Password
            sender_name: Nome do remetente
            max_emails_per_hour: Limite de emails por hora
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.sender_name = sender_name or sender_email.split("@")[0]
        self.max_emails_per_hour = max_emails_per_hour
        
        # Fila de emails enviados (para controlar limite)
        self.emails_enviados = []
        
        # Detectar provedor
        self.provedor = self._detectar_provedor()
        
        logger.info(f"Handler SMTP inicializado para: {sender_email} ({self.provedor})")

    def _detectar_provedor(self) -> str:
        """Detecta provedor de email"""
        email_lower = self.sender_email.lower()
        
        if "gmail" in email_lower:
            return "gmail"
        elif "outlook" in email_lower or "hotmail" in email_lower:
            return "outlook"
        else:
            return "custom"

    def pode_enviar(self) -> bool:
        """
        Verifica se pode enviar email (respeita limite por hora)
        
        Returns:
            True se pode enviar, False se limite atingido
        """
        agora = datetime.now()
        uma_hora_atras = agora - timedelta(hours=1)
        
        # Limpar registros antigos
        self.emails_enviados = [
            timestamp for timestamp in self.emails_enviados
            if timestamp > uma_hora_atras
        ]
        
        return len(self.emails_enviados) < self.max_emails_per_hour

    def obter_tempo_espera(self) -> int:
        """
        Calcula tempo de espera até poder enviar novamente
        
        Returns:
            Tempo em segundos
        """
        if not self.emails_enviados:
            return 0
        
        agora = datetime.now()
        email_mais_antigo = min(self.emails_enviados)
        uma_hora_depois = email_mais_antigo + timedelta(hours=1)
        
        tempo_espera = (uma_hora_depois - agora).total_seconds()
        return max(0, int(tempo_espera))

    def simular_envio(
        self,
        destinatario: str,
        assunto: str,
        corpo: str,
        arquivo_anexo: Path = None,
        empresa_nome: str = None
    ) -> Dict:
        """
        Simula envio de email (para testes)
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo: Corpo do email
            arquivo_anexo: Caminho do arquivo para anexar
            empresa_nome: Nome da empresa (para logging)
            
        Returns:
            Dict com status do envio
        """
        resultado = {
            "sucesso": True,
            "mensagem": f"[SIMULADO] Email enviado com sucesso",
            "destinatario": destinatario,
            "timestamp": datetime.now().isoformat(),
            "empresa": empresa_nome,
            "tipo": "simulado"
        }
        
        logger.info(f"[SIMULADO] Email para {destinatario} - {empresa_nome}")
        logger.debug(f"Assunto: {assunto}")
        logger.debug(f"Corpo:\n{corpo}")
        
        if arquivo_anexo:
            if Path(arquivo_anexo).exists():
                logger.debug(f"Anexo: {arquivo_anexo}")
            else:
                logger.warning(f"Arquivo não encontrado: {arquivo_anexo}")
        
        # Registrar como enviado (para controle de limite)
        self.emails_enviados.append(datetime.now())
        
        return resultado

    def enviar_email(
        self,
        destinatario: str,
        assunto: str,
        corpo: str,
        arquivo_anexo: Path = None,
        empresa_nome: str = None
    ) -> Dict:
        """
        Envia email (implementação real)
        
        NOTA: Implementação completa requer instalação de SMTP
        Esta versão inclui o código estruturado para fácil integração
        
        Args:
            destinatario: Email do destinatário
            assunto: Assunto do email
            corpo: Corpo do email
            arquivo_anexo: Caminho do arquivo para anexar
            empresa_nome: Nome da empresa (para logging)
            
        Returns:
            Dict com status do envio
        """
        resultado = {
            "sucesso": False,
            "mensagem": "",
            "destinatario": destinatario,
            "timestamp": datetime.now().isoformat(),
            "empresa": empresa_nome,
            "tipo": "real"
        }
        
        # Verificar limite
        if not self.pode_enviar():
            tempo_espera = self.obter_tempo_espera()
            resultado["mensagem"] = f"Limite de emails/hora atingido. Aguarde {tempo_espera}s"
            logger.warning(resultado["mensagem"])
            return resultado
        
        try:
            # Implementação com yagmail (mais simples)
            import yagmail
            
            # Criar mensagem
            conteudo = [corpo]
            
            # Adicionar anexo se fornecido
            if arquivo_anexo and Path(arquivo_anexo).exists():
                conteudo.append(yagmail.inline(str(arquivo_anexo)))
            
            # Enviar
            yag = yagmail.SMTP(self.sender_email, self.sender_password)
            yag.send(
                to=destinatario,
                subject=assunto,
                contents=conteudo,
                prettify_html=True
            )
            yag.close()
            
            resultado["sucesso"] = True
            resultado["mensagem"] = "Email enviado com sucesso"
            
            # Registrar envio
            self.emails_enviados.append(datetime.now())
            
            logger.info(f"Email enviado para {destinatario} - {empresa_nome}")
            
        except ImportError:
            resultado["mensagem"] = "yagmail não instalado. Use: pip install yagmail"
            logger.error(resultado["mensagem"])
        except Exception as e:
            resultado["mensagem"] = f"Erro ao enviar: {str(e)}"
            logger.error(resultado["mensagem"])
        
        return resultado

    def obter_status(self) -> Dict:
        """
        Retorna status atual do handler
        
        Returns:
            Dict com estatísticas
        """
        agora = datetime.now()
        uma_hora_atras = agora - timedelta(hours=1)
        
        # Contar emails da última hora
        emails_ultima_hora = len([
            t for t in self.emails_enviados
            if t > uma_hora_atras
        ])
        
        return {
            "provedor": self.provedor,
            "emails_ultima_hora": emails_ultima_hora,
            "limite_por_hora": self.max_emails_per_hora,
            "pode_enviar": self.pode_enviar(),
            "tempo_espera_segundos": self.obter_tempo_espera() if not self.pode_enviar() else 0
        }
