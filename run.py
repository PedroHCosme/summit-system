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

# Configuração do ambiente (dev = localhost, prod = 0.0.0.0)
try:
    from config_local import DEVELOPMENT_MODE, WEB_PORT
except ImportError:
    # Se não houver config local, assumimos PRODUÇÃO (acesso externo via tunnel)
    DEVELOPMENT_MODE = False
    WEB_PORT = 5000

BIND_HOST = '127.0.0.1' if DEVELOPMENT_MODE else '0.0.0.0'

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
        
        # Configurar logs: Mostrar no console em Dev, suprimir em Prod
        log_output = None if DEVELOPMENT_MODE else subprocess.DEVNULL
        
        # Windows não suporta Gunicorn nativamente
        is_windows = os.name == 'nt'
        
        # Tenta com gunicorn primeiro (apenas se não for Windows)
        if not is_windows:
            try:
                web_server_process = subprocess.Popen(
                    [
                        'gunicorn',
                        '--workers', '2',
                        '--bind', f'{BIND_HOST}:{WEB_PORT}',
                        '--access-logfile', '-',
                        '--error-logfile', '-',
                        '--log-level', 'warning',
                        'src.web.app:app'
                    ],
                    cwd=project_dir,
                    env=env,
                    stdout=log_output,
                    stderr=log_output
                )
                print(f"✓ Servidor web iniciado com Gunicorn (http://{BIND_HOST}:{WEB_PORT})")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"⚠ Falha ao tentar Gunicorn: {e}")

        # Fallback ou Windows: Flask dev server
        if web_server_process is None:
            if is_windows:
                print("  ℹ️  Windows detectado: Usando Flask Dev Server...")
                
            web_server_process = subprocess.Popen(
                [sys.executable, '-m', 'flask', 'run', f'--host={BIND_HOST}', f'--port={WEB_PORT}'],
                cwd=project_dir,
                env={**env, 'FLASK_APP': 'src.web.app:app'},
                stdout=log_output,
                stderr=log_output
            )
            print(f"✓ Servidor web iniciado com Flask dev server (http://{BIND_HOST}:{WEB_PORT})")
            
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
