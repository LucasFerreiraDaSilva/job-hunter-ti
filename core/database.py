"""
Módulo de gerenciamento do banco de dados SQLite
Responsável por criar, inicializar e executar operações no banco
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

from config.settings import DATABASE_PATH, LOGS_DIR

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Database:
    """Gerenciador do banco de dados SQLite"""

    def __init__(self, db_path: Path = DATABASE_PATH):
        """
        Inicializa conexão com banco de dados
        
        Args:
            db_path: Caminho do arquivo do banco de dados
        """
        self.db_path = db_path
        self.connection = None
        self._initialize()

    def _initialize(self) -> None:
        """Inicializa o banco de dados e cria tabelas se não existirem"""
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row
            self._create_tables()
            logger.info(f"Banco de dados inicializado: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            raise

    def _create_tables(self) -> None:
        """Cria tabelas se não existirem"""
        cursor = self.connection.cursor()

        # Tabela de empresas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS empresas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                site TEXT,
                telefone TEXT,
                cidade TEXT,
                estado TEXT,
                url_maps TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela de emails
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                tipo TEXT,
                confianca REAL DEFAULT 0.5,
                pagina_origem TEXT,
                status TEXT DEFAULT 'valido',
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                UNIQUE(empresa_id, email)
            )
        """)

        # Tabela de envios
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS envios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                empresa_id INTEGER NOT NULL,
                email_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pendente',
                data_envio TIMESTAMP,
                resposta TEXT,
                erros TEXT,
                tentativas INTEGER DEFAULT 0,
                proxima_tentativa TIMESTAMP,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (empresa_id) REFERENCES empresas(id),
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        """)

        # Tabela de logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                mensagem TEXT,
                detalhes TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.connection.commit()
        logger.info("Tabelas criadas/verificadas com sucesso")

    def close(self) -> None:
        """Fecha conexão com banco de dados"""
        if self.connection:
            self.connection.close()
            logger.info("Conexão com banco de dados fechada")

    # ============= OPERAÇÕES EMPRESAS =============

    def adicionar_empresa(
        self,
        nome: str,
        site: str = None,
        telefone: str = None,
        cidade: str = None,
        estado: str = None,
        url_maps: str = None
    ) -> Optional[int]:
        """
        Adiciona uma empresa ao banco
        
        Args:
            nome: Nome da empresa
            site: URL do site
            telefone: Telefone
            cidade: Cidade
            estado: Estado
            url_maps: URL do Google Maps
            
        Returns:
            ID da empresa ou None se falhar
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO empresas (nome, site, telefone, cidade, estado, url_maps)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nome, site, telefone, cidade, estado, url_maps))
            self.connection.commit()
            empresa_id = cursor.lastrowid
            logger.info(f"Empresa adicionada: {nome} (ID: {empresa_id})")
            return empresa_id
        except sqlite3.IntegrityError:
            logger.warning(f"Empresa já existe: {nome}")
            return self.obter_empresa_por_nome(nome)
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar empresa: {e}")
            return None

    def obter_empresa_por_nome(self, nome: str) -> Optional[int]:
        """Obtém ID da empresa pelo nome"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT id FROM empresas WHERE nome = ?", (nome,))
            resultado = cursor.fetchone()
            return resultado[0] if resultado else None
        except sqlite3.Error as e:
            logger.error(f"Erro ao buscar empresa: {e}")
            return None

    def obter_todas_empresas(self) -> List[Dict]:
        """Obtém todas as empresas"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM empresas ORDER BY data_criacao DESC")
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao listar empresas: {e}")
            return []

    # ============= OPERAÇÕES EMAILS =============

    def adicionar_email(
        self,
        empresa_id: int,
        email: str,
        tipo: str = None,
        confianca: float = 0.5,
        pagina_origem: str = None
    ) -> Optional[int]:
        """
        Adiciona um email ao banco
        
        Args:
            empresa_id: ID da empresa
            email: Endereço de email
            tipo: Tipo de email (rh, contato, etc)
            confianca: Score de confiança (0-1)
            pagina_origem: Página onde foi encontrado
            
        Returns:
            ID do email ou None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO emails (empresa_id, email, tipo, confianca, pagina_origem)
                VALUES (?, ?, ?, ?, ?)
            """, (empresa_id, email, tipo, confianca, pagina_origem))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.debug(f"Email duplicado: {email} para empresa ID {empresa_id}")
            return None
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar email: {e}")
            return None

    def obter_emails_por_empresa(self, empresa_id: int) -> List[Dict]:
        """Obtém todos os emails de uma empresa"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM emails 
                WHERE empresa_id = ? 
                ORDER BY confianca DESC
            """, (empresa_id,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao listar emails: {e}")
            return []

    def obter_emails_prioritarios(self, limite: int = 100) -> List[Dict]:
        """Obtém emails de maior confiança para envio"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT e.* FROM emails e
                WHERE e.status = 'valido'
                ORDER BY e.confianca DESC
                LIMIT ?
            """, (limite,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter emails prioritários: {e}")
            return []

    # ============= OPERAÇÕES ENVIOS =============

    def registrar_envio(
        self,
        empresa_id: int,
        email_id: int,
        status: str = "pendente",
        data_envio: datetime = None,
        erros: str = None
    ) -> Optional[int]:
        """
        Registra um envio de email
        
        Args:
            empresa_id: ID da empresa
            email_id: ID do email
            status: Status do envio
            data_envio: Data/hora do envio
            erros: Mensagem de erro (se houver)
            
        Returns:
            ID do registro ou None
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO envios (empresa_id, email_id, status, data_envio, erros, tentativas)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (empresa_id, email_id, status, data_envio, erros))
            self.connection.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Erro ao registrar envio: {e}")
            return None

    def obter_envios_pendentes(self, limite: int = 10) -> List[Dict]:
        """Obtém envios pendentes"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT * FROM envios 
                WHERE status = 'pendente' 
                ORDER BY data_criacao ASC 
                LIMIT ?
            """, (limite,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter envios pendentes: {e}")
            return []

    def atualizar_status_envio(
        self,
        envio_id: int,
        status: str,
        resposta: str = None,
        erros: str = None
    ) -> bool:
        """
        Atualiza status de um envio
        
        Args:
            envio_id: ID do envio
            status: Novo status
            resposta: Resposta recebida
            erros: Erros ocorridos
            
        Returns:
            True se sucesso, False se falhar
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                UPDATE envios 
                SET status = ?, resposta = ?, erros = ?, data_envio = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, resposta, erros, envio_id))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao atualizar envio: {e}")
            return False

    # ============= OPERAÇÕES LOGS =============

    def adicionar_log(
        self,
        tipo: str,
        mensagem: str,
        detalhes: Dict = None
    ) -> bool:
        """
        Adiciona um registro de log ao banco
        
        Args:
            tipo: Tipo de log (INFO, ERROR, WARNING, etc)
            mensagem: Mensagem principal
            detalhes: Detalhes em formato dict
            
        Returns:
            True se sucesso
        """
        try:
            cursor = self.connection.cursor()
            detalhes_json = json.dumps(detalhes) if detalhes else None
            cursor.execute("""
                INSERT INTO logs (tipo, mensagem, detalhes)
                VALUES (?, ?, ?)
            """, (tipo, mensagem, detalhes_json))
            self.connection.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Erro ao adicionar log: {e}")
            return False

    def obter_logs(self, tipo: str = None, limite: int = 100) -> List[Dict]:
        """Obtém logs do banco"""
        try:
            cursor = self.connection.cursor()
            if tipo:
                cursor.execute("""
                    SELECT * FROM logs 
                    WHERE tipo = ? 
                    ORDER BY data_criacao DESC 
                    LIMIT ?
                """, (tipo, limite))
            else:
                cursor.execute("""
                    SELECT * FROM logs 
                    ORDER BY data_criacao DESC 
                    LIMIT ?
                """, (limite,))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter logs: {e}")
            return []

    # ============= ESTATÍSTICAS =============

    def obter_estatisticas(self) -> Dict:
        """Obtém estatísticas gerais do banco"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM empresas")
            total_empresas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM emails WHERE status = 'valido'")
            total_emails_validos = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM envios WHERE status = 'enviado'")
            total_enviados = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM envios WHERE status = 'pendente'")
            total_pendentes = cursor.fetchone()[0]
            
            return {
                "total_empresas": total_empresas,
                "total_emails_validos": total_emails_validos,
                "total_enviados": total_enviados,
                "total_pendentes": total_pendentes
            }
        except sqlite3.Error as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}
