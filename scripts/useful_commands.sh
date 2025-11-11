#!/bin/bash
# Comandos úteis para as novas funcionalidades

# ============================================================
# MIGRAÇÃO DE DADOS
# ============================================================

# Migração completa (apaga e recria tudo)
python scripts/migrate_data.py

# Migração incremental (preserva dados existentes)
python scripts/migrate_data.py --append

# Ver ajuda
python scripts/migrate_data.py --help

# ============================================================
# VALIDAÇÃO E TESTES
# ============================================================

# Executar testes de validação
python tests/validate_improvements.py

# Executar exemplos de transações
python examples/transaction_usage.py

# ============================================================
# CONSULTAS NO BANCO
# ============================================================

# Contar membros
sqlite3 gym_database.db "SELECT COUNT(*) as total_membros FROM membros;"

# Contar check-ins
sqlite3 gym_database.db "SELECT COUNT(*) as total_checkins FROM frequencia;"

# Ver últimos membros adicionados
sqlite3 gym_database.db "SELECT nome, plano, created_at FROM membros ORDER BY created_at DESC LIMIT 10;"

# Ver últimos check-ins
sqlite3 gym_database.db "SELECT m.nome, f.checkin_datetime FROM frequencia f JOIN membros m ON f.member_id = m.id ORDER BY f.checkin_datetime DESC LIMIT 10;"

# Verificar duplicatas de check-ins por data
sqlite3 gym_database.db "SELECT member_id, checkin_datetime, COUNT(*) as vezes FROM frequencia GROUP BY member_id, checkin_datetime HAVING COUNT(*) > 1;"

# ============================================================
# BACKUP E RESTORE
# ============================================================

# Criar backup antes de migração
cp gym_database.db gym_database.db.backup.$(date +%Y%m%d_%H%M%S)

# Restaurar backup
# cp gym_database.db.backup.YYYYMMDD_HHMMSS gym_database.db

# ============================================================
# LOGS E MONITORAMENTO
# ============================================================

# Executar migração com log
python scripts/migrate_data.py --append 2>&1 | tee logs/migration_$(date +%Y%m%d_%H%M%S).log

# Criar diretório de logs se não existir
mkdir -p logs

# ============================================================
# AUTOMAÇÃO (CRON)
# ============================================================

# Exemplo de cron para migração diária incremental (1h da manhã)
# 0 1 * * * cd /path/to/summit-projv2 && python scripts/migrate_data.py --append >> logs/migration_cron.log 2>&1

# ============================================================
# LIMPEZA
# ============================================================

# Remover arquivos de teste
rm -f test_db.db

# Limpar cache Python
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete

# ============================================================
# DESENVOLVIMENTO
# ============================================================

# Verificar sintaxe Python
python -m py_compile scripts/migrate_data.py
python -m py_compile src/data/database_manager.py

# Verificar tipos (se mypy instalado)
# mypy scripts/migrate_data.py
# mypy src/data/database_manager.py

# ============================================================
# INFO RÁPIDA
# ============================================================

# Ver estatísticas do banco
sqlite3 gym_database.db << EOF
SELECT 
    'Membros' as tipo, 
    COUNT(*) as total,
    (SELECT COUNT(DISTINCT plano) FROM membros) as variedade
FROM membros
UNION ALL
SELECT 
    'Check-ins' as tipo,
    COUNT(*) as total,
    COUNT(DISTINCT member_id) as variedade
FROM frequencia;
EOF

# Ver distribuição por plano
sqlite3 gym_database.db "SELECT plano, COUNT(*) as quantidade FROM membros GROUP BY plano ORDER BY quantidade DESC;"

# Ver taxa de check-in por membro
sqlite3 gym_database.db << EOF
SELECT 
    m.nome,
    m.plano,
    COUNT(f.id) as total_checkins
FROM membros m
LEFT JOIN frequencia f ON m.id = f.member_id
GROUP BY m.id, m.nome, m.plano
ORDER BY total_checkins DESC
LIMIT 20;
EOF
