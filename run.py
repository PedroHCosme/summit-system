#!/usr/bin/env python3
"""
Script de entrada principal do Summit System.
Executa a GUI e o serviço web simultaneamente.
"""
import sys
import os
import subprocess
import signal
import atexit

# Adiciona o diretório do projeto ao Python path para que `src` seja um módulo
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

from src.data.migrations import DatabaseMigrator
from src.data.database_manager import DatabaseManager

# Variável global para o processo do servidor web
web_server_process = None


def run_migrations():
    """Executa migrações críticas antes de iniciar qualquer serviço."""
    print("🔄 Verificando banco de dados...")
    try:
        # Instanciar DatabaseManager apenas para migrações
        db_manager = DatabaseManager()
        db_manager.connect()
        
        migrator = DatabaseMigrator(db_manager)
        
        # Executa APENAS a criação de tabelas e colunas críticas aqui
        # O resto pode ser feito pela GUI depois
        print("  - Garantindo tabelas...")
        migrator.ensure_all_tables_exist()
        
        print("  - Garantindo colunas...")
        migrator.ensure_all_member_columns()
        
        # Garante planos básicos para o web service não falhar ao listar planos
        print("  - Garantindo planos base...") 
        migrator.seed_all_plans()
        
        db_manager.close()
        print("✓ Banco de dados pronto.")
    except Exception as e:
        print(f"⚠ Erro na preparação do banco de dados: {e}")
        # Não abortamos, pois a GUI pode tentar corrigir ou mostrar erro melhor


def start_web_server():
    """Inicia o servidor web (gunicorn) em processo separado."""
    global web_server_process
    
    print("🌐 Iniciando servidor web...")
    
    try:
        # Usar gunicorn se disponível, senão Flask dev server
        env = os.environ.copy()
        env['PYTHONPATH'] = project_dir + ':' + env.get('PYTHONPATH', '')
        
        # Tenta com gunicorn primeiro (produção)
        try:
            web_server_process = subprocess.Popen(
                [
                    'gunicorn',
                    '--workers', '2',
                    '--bind', '0.0.0.0:5000',
                    '--access-logfile', '-',
                    '--error-logfile', '-',
                    '--log-level', 'warning',
                    'src.web.app:app'
                ],
                cwd=project_dir,
                env=env,
                stdout=subprocess.DEVNULL,  # Suprimir output para não poluir console
                stderr=subprocess.DEVNULL
            )
            print("✓ Servidor web iniciado com Gunicorn (http://localhost:5000)")
        except FileNotFoundError:
            # Fallback para Flask dev server
            web_server_process = subprocess.Popen(
                [sys.executable, '-m', 'flask', 'run', '--host=0.0.0.0', '--port=5000'],
                cwd=project_dir,
                env={**env, 'FLASK_APP': 'src.web.app:app'},
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("✓ Servidor web iniciado com Flask dev server (http://localhost:5000)")
            
    except Exception as e:
        print(f"⚠ Erro ao iniciar servidor web: {e}")
        print("  O sistema continuará funcionando apenas com a GUI local.")


def stop_web_server():
    """Para o servidor web ao encerrar."""
    global web_server_process
    
    if web_server_process is not None:
        print("\n🛑 Encerrando servidor web...")
        try:
            web_server_process.terminate()
            web_server_process.wait(timeout=5)
            print("✓ Servidor web encerrado.")
        except subprocess.TimeoutExpired:
            web_server_process.kill()
        except Exception as e:
            print(f"⚠ Erro ao encerrar servidor: {e}")


def signal_handler(signum, frame):
    """Handler para sinais de encerramento (Ctrl+C)."""
    stop_web_server()
    sys.exit(0)


# Registrar handlers de encerramento
atexit.register(stop_web_server)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    # 0. Preparar banco de dados (evitar erro no web service)
    run_migrations()

    # 1. Iniciar servidor web em background
    start_web_server()
    
    # 2. Iniciar GUI (bloqueante - fica aqui até fechar a janela)
    print("\n🖥️  Iniciando interface gráfica...")
    from src.ui.gui import main
    main()
    
    # 3. Ao sair da GUI, encerrar servidor web
    stop_web_server()
