# Summit System - Contexto para Codex

## O que e este projeto

Sistema de gestao para a **Summit**, uma academia de escalada. Gerencia membros, planos, check-ins, pagamentos e relatorios. Tem duas interfaces:

- **Desktop (PyQt6)** — usada pelo dono da academia no dia a dia
- **Web (Flask)** — usada pelos proprios membros para se cadastrar e fazer check-in pelo celular

**Escala**: ~15-30 check-ins/dia. Banco SQLite local.

## Documentacao auxiliar

Antes de trabalhar em qualquer feature, leia os documentos relevantes:

| Arquivo | Conteudo |
|---------|----------|
| `.Codex/docs/BUSINESS_RULES.md` | Regras de negocio, tipos de plano, status de membro vs plano |
| `.Codex/docs/ARCHITECTURE.md` | Mapa da codebase, camadas, dependencias entre arquivos |
| `.Codex/docs/REPORTS_STATUS.md` | Estado atual dos relatorios, problemas conhecidos, roadmap |
| `.Codex/docs/DATA_DICTIONARY.md` | Tabelas do banco, campos, tipos, relacionamentos |

## Convencoes do projeto

- **Linguagem do codigo**: Python, comentarios e docstrings em portugues
- **Framework UI**: PyQt6 com QSS para estilos
- **ORM**: SQLAlchemy (modelos em `src/data/models.py`)
- **Templates HTML**: Jinja2 (relatorios em `src/templates/reports/`)
- **Servicos**: `src/services/` — camada de negocio (MemberService, PaymentService, CheckinService, PlanService)
- **Config**: `src/config.py` — sendo migrado para tabela `Plano` no banco
- **Data layer legado**: `DatabaseManager` em `src/data/database_manager.py` — DEPRECATED, usar services

## Regras criticas (resumo)

1. **Status do Plano != Status do Membro** — sao conceitos separados. Ver `BUSINESS_RULES.md`.
2. **Planos quota** (Pacote 10 etc) nao tem vencimento — usam `voucher_credits`.
3. **Treino** e um servico separado (R$90/mes), com vencimento independente do plano.
4. **Membros PENDENTE** (cadastro web nao aprovado) nao aparecem em relatorios.
5. **1 check-in por membro por dia** — regra dura no CheckinService.
6. **Planos per-checkin** (Diaria R$35, Gympass/Totalpass R$15) geram Pagamento automatico no check-in.

## Git

Commits neste repo usam gitconfig pessoal:
```bash
git -c include.path=C:/Users/Usuario/pedrocosme/.gitconfig-pessoal commit -m "msg"
```
