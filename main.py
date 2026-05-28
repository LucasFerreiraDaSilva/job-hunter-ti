"""
Job Hunter TI - Sistema de busca e envio de currículo
Automatiza busca de empresas, extração de emails e envio de currículo
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/jobhunter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from config.settings import DATABASE_PATH, LOGS_DIR
from core.database import Database
from scrapers.company_scraper import CompanyScraper
from email_extractor.extractor import EmailExtractor
from email_sender.smtp_handler import SMTPHandler


def exibir_banner():
    """Exibe banner inicial"""
    banner = """
    ╔══════════════════════════════════════════════════╗
    ║         🎯 JOB HUNTER TI - v1.0 🎯              ║
    ║  Automatizador de Busca e Envio de Currículo    ║
    ╚══════════════════════════════════════════════════╝
    """
    print(banner)


def menu_principal():
    """Exibe menu principal"""
    menu = """
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
    """
    print(menu)


def buscar_empresas(db: Database, scraper: CompanyScraper):
    """Busca empresas"""
    print("\n" + "="*50)
    print("BUSCAR EMPRESAS")
    print("="*50)
    
    palavra_chave = input("Palavra-chave (ex: software, TI, infraestrutura): ").strip()
    cidade = input("Cidade (ex: São Paulo, Rio de Janeiro): ").strip()
    
    if not palavra_chave:
        print("❌ Palavra-chave obrigatória")
        return
    
    print("\n⏳ Buscando empresas...")
    
    try:
        empresas = scraper.buscar_empresas_google(palavra_chave, cidade, limite=5)
        
        if not empresas:
            print("❌ Nenhuma empresa encontrada")
            return
        
        print(f"\n✅ Encontradas {len(empresas)} empresas:\n")
        
        for idx, empresa in enumerate(empresas, 1):
            print(f"{idx}. {empresa['nome']}")
            print(f"   Site: {empresa['site']}")
            print(f"   Cidade: {empresa['cidade']}")
            
            # Adicionar ao banco
            empresa_id = db.adicionar_empresa(
                nome=empresa['nome'],
                site=empresa['site'],
                cidade=empresa['cidade']
            )
            
            if empresa_id:
                print(f"   ✅ Adicionada ao banco (ID: {empresa_id})")
            else:
                print(f"   ⚠️  Já existe no banco")
            
            print()
        
        db.adicionar_log(
            "BUSCA",
            f"Busca realizada: {palavra_chave} em {cidade}",
            {"total": len(empresas), "palavra_chave": palavra_chave, "cidade": cidade}
        )
        
    except Exception as e:
        print(f"❌ Erro ao buscar empresas: {e}")
        logger.error(f"Erro: {e}")


def extrair_emails(db: Database, extractor: EmailExtractor):
    """Extrai emails de uma empresa"""
    print("\n" + "="*50)
    print("EXTRAIR EMAILS DE EMPRESA")
    print("="*50)
    
    # Listar empresas
    empresas = db.obter_todas_empresas()
    if not empresas:
        print("❌ Nenhuma empresa cadastrada")
        return
    
    print("\nEmpresas cadastradas:\n")
    for idx, empresa in enumerate(empresas, 1):
        print(f"{idx}. {empresa['nome']} - {empresa['site']}")
    
    escolha = input("\nEscolha o número da empresa (0 para cancelar): ").strip()
    
    try:
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(empresas):
            print("❌ Opção inválida")
            return
        
        empresa = empresas[idx]
        empresa_id = empresa['id']
        site = empresa['site']
        
        if not site:
            print("❌ Empresa sem site cadastrado")
            return
        
        print(f"\n⏳ Extraindo emails de {empresa['nome']}...")
        
        # Extrair emails
        emails = extractor.extrair_emails_do_site(site)
        
        if not emails:
            print("❌ Nenhum email encontrado")
            return
        
        print(f"\n✅ Encontrados {len(emails)} emails:\n")
        
        for email_info in emails:
            email = email_info['email']
            confianca = email_info['confianca']
            tipo = email_info['tipo']
            
            # Adicionar ao banco
            db.adicionar_email(
                empresa_id=empresa_id,
                email=email,
                tipo=tipo,
                confianca=confianca,
                pagina_origem=email_info.get('pagina', 'desconhecida')
            )
            
            print(f"  • {email}")
            print(f"    Tipo: {tipo} | Confiança: {confianca:.0%}")
        
        db.adicionar_log(
            "EXTRACAO_EMAIL",
            f"Emails extraídos: {empresa['nome']}",
            {"empresa_id": empresa_id, "total_emails": len(emails)}
        )
        
    except ValueError:
        print("❌ Entrada inválida")
    except Exception as e:
        print(f"❌ Erro ao extrair emails: {e}")
        logger.error(f"Erro: {e}")


def visualizar_empresas(db: Database):
    """Visualiza empresas armazenadas"""
    print("\n" + "="*50)
    print("EMPRESAS ARMAZENADAS")
    print("="*50)
    
    empresas = db.obter_todas_empresas()
    
    if not empresas:
        print("❌ Nenhuma empresa cadastrada")
        return
    
    print(f"\n📊 Total: {len(empresas)} empresas\n")
    
    for empresa in empresas:
        print(f"🏢 {empresa['nome']}")
        print(f"   ID: {empresa['id']}")
        print(f"   Site: {empresa['site']}")
        print(f"   Cidade: {empresa['cidade']}")
        print(f"   Data: {empresa['data_criacao']}")
        print()


def visualizar_emails(db: Database):
    """Visualiza emails armazenados"""
    print("\n" + "="*50)
    print("EMAILS ARMAZENADOS")
    print("="*50)
    
    empresas = db.obter_todas_empresas()
    
    if not empresas:
        print("❌ Nenhuma empresa cadastrada")
        return
    
    print("Empresas:\n")
    for idx, empresa in enumerate(empresas, 1):
        print(f"{idx}. {empresa['nome']}")
    
    escolha = input("\nEscolha o número (0 para todos, 0 para cancelar): ").strip()
    
    try:
        if escolha == "0":
            # Mostrar todos
            emails = []
            for empresa in empresas:
                emails.extend(db.obter_emails_por_empresa(empresa['id']))
        else:
            idx = int(escolha) - 1
            if idx < 0 or idx >= len(empresas):
                print("❌ Opção inválida")
                return
            emails = db.obter_emails_por_empresa(empresas[idx]['id'])
        
        if not emails:
            print("❌ Nenhum email encontrado")
            return
        
        print(f"\n📧 Total: {len(emails)} emails\n")
        
        for email in emails:
            print(f"  • {email['email']}")
            print(f"    Tipo: {email['tipo']} | Confiança: {email['confianca']:.0%}")
        
    except ValueError:
        print("❌ Entrada inválida")


def enviar_curriculo_simulado(db: Database):
    """Simula envio de currículo"""
    print("\n" + "="*50)
    print("ENVIAR CURRÍCULO (SIMULADO)")
    print("="*50)
    
    # Por enquanto, apenas simulação
    print("\n⚠️  Modo SIMULADO ativado")
    print("Para envio real, configure suas credenciais\n")
    
    emails_prioritarios = db.obter_emails_prioritarios(limite=3)
    
    if not emails_prioritarios:
        print("❌ Nenhum email disponível")
        return
    
    print(f"Emails prioritários para envio:\n")
    
    for email in emails_prioritarios:
        print(f"  • {email['email']} (Confiança: {email['confianca']:.0%})")
        print(f"    Para: Empresa ID {email['empresa_id']}")
    
    print("\n✅ Simulação realizada com sucesso")
    
    db.adicionar_log(
        "ENVIO_SIMULADO",
        "Envio simulado de currículo",
        {"total_emails": len(emails_prioritarios)}
    )


def visualizar_estatisticas(db: Database):
    """Mostra estatísticas"""
    print("\n" + "="*50)
    print("ESTATÍSTICAS")
    print("="*50)
    
    stats = db.obter_estatisticas()
    
    print(f"\n📊 RESUMO:\n")
    print(f"  • Empresas cadastradas: {stats.get('total_empresas', 0)}")
    print(f"  • Emails válidos: {stats.get('total_emails_validos', 0)}")
    print(f"  • Envios realizados: {stats.get('total_enviados', 0)}")
    print(f"  • Envios pendentes: {stats.get('total_pendentes', 0)}")


def limpar_banco(db: Database):
    """Limpa base de dados (confirmação)"""
    print("\n" + "="*50)
    print("LIMPAR BASE DE DADOS")
    print("="*50)
    
    confirmacao = input("\n⚠️  Deseja realmente deletar TODO O BANCO? (SIM/NÃO): ").strip().upper()
    
    if confirmacao == "SIM":
        try:
            # Fechar conexão
            db.close()
            
            # Deletar arquivo
            if DATABASE_PATH.exists():
                DATABASE_PATH.unlink()
                print("✅ Base de dados deletada")
                
            # Reinicializar
            db = Database()
            print("✅ Novo banco criado")
            
            return db
        except Exception as e:
            print(f"❌ Erro ao limpar: {e}")
    else:
        print("❌ Operação cancelada")
    
    return db


def main():
    """Função principal"""
    exibir_banner()
    
    # Inicializar componentes
    try:
        db = Database()
        scraper = CompanyScraper()
        extractor = EmailExtractor()
        
        logger.info("Aplicação iniciada")
        
        while True:
            menu_principal()
            opcao = input("\nEscolha uma opção: ").strip()
            
            if opcao == "1":
                buscar_empresas(db, scraper)
            elif opcao == "2":
                extrair_emails(db, extractor)
            elif opcao == "3":
                visualizar_empresas(db)
            elif opcao == "4":
                visualizar_emails(db)
            elif opcao == "5":
                enviar_curriculo_simulado(db)
            elif opcao == "6":
                visualizar_estatisticas(db)
            elif opcao == "7":
                db = limpar_banco(db)
            elif opcao == "0":
                print("\n👋 Até logo!\n")
                break
            else:
                print("❌ Opção inválida")
        
        # Fechar recursos
        db.close()
        scraper.fechar()
        extractor.fechar()
        logger.info("Aplicação finalizada")
        
    except KeyboardInterrupt:
        print("\n\n👋 Aplicação interrompida pelo usuário")
        logger.info("Aplicação interrompida")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        logger.error(f"Erro fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
