# Changelog

Todas as mudanças relevantes deste projeto serão documentadas aqui.

## [0.1.0] — 2026-05-20

Primeira versão pública. Servidor MCP somente leitura para o Zendesk com 13 ferramentas.

### Adicionado

**Ferramentas de Tickets**
- `get_ticket` — detalhes completos: assunto, status, prioridade, solicitante, responsável, organização, tags, CSAT, descrição
- `get_ticket_comments` — thread de comentários com suporte a notas internas (`include_internal`)
- `get_ticket_metrics` — métricas SLA: primeiro tempo de resposta, tempo de resolução, reaberturas
- `get_ticket_audits` — trilha de auditoria completa com alterações de campo (`antigo → novo`)
- `search_tickets` — busca com sintaxe nativa do Zendesk (`status:open assignee:me tag:billing`)
- `list_tickets` — listagem ordenada por última atualização, com filtro opcional por status
- `get_linked_incidents` — incidentes vinculados a um ticket de problema
- `get_tickets_count_by_status` — contagem de tickets por status + total geral

**Ferramentas de Usuários**
- `get_user` — detalhes do usuário com organização resolvida, papel, tags, status
- `search_users` — busca por nome, e-mail ou outros atributos

**Ferramentas de Organizações**
- `get_organization` — detalhes da organização: domínios, tags, notas, grupo
- `list_organizations` — lista paginada de todas as organizações

**Ferramentas de Métricas**
- `list_satisfaction_ratings` — avaliações CSAT com filtro por score (`good` / `bad`)

**Infraestrutura**
- `ZendeskClient` somente leitura com retry/backoff exponencial para 429 e 5xx
- Validação de configuração no startup via `pydantic-settings` — falha rápida com mensagem clara
- Transporte stdio via FastMCP 3.3+
- CI com ruff, mypy, pytest e pip-audit via GitHub Actions
- Publicação automática no PyPI via Trusted Publishing ao criar tag `v*`
- 64 testes unitários e de integração (100% offline)
- Tool annotations (`readOnlyHint=True`) em todas as ferramentas
