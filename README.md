# zendesk-mcp-server

![CI](https://github.com/jonhnatta/zendesk-mcp-server/actions/workflows/ci.yml/badge.svg)
[![PyPI version](https://img.shields.io/pypi/v/zendesk-mcp-ro?style=flat)](https://pypi.org/project/zendesk-mcp-ro/)
[![Python](https://img.shields.io/badge/Python-%3E%3D3.12-3776AB?style=flat)](https://www.python.org/)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.3+-009688?style=flat)](https://github.com/jlowin/fastmcp)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?style=flat)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/badge/Ruff-linter-D7FF64?style=flat&logoColor=000)](https://github.com/astral-sh/ruff)

Servidor MCP somente leitura para o Zendesk. Expõe 13 ferramentas via protocolo MCP com transporte stdio — tickets, usuários, organizações e avaliações CSAT — sem risco de modificação acidental de dados.

---

## Quick start

```bash
uvx zendesk-mcp-ro
```

---

## Configurando o servidor MCP

Adicione a entrada abaixo na configuração do seu cliente MCP:

```json
{
  "mcpServers": {
    "zendesk": {
      "command": "uvx",
      "args": ["zendesk-mcp-ro"],
      "env": {
        "ZENDESK_EMAIL": "voce@empresa.com",
        "ZENDESK_TOKEN": "seu-api-token",
        "ZENDESK_SUBDOMAIN": "sua-empresa"
      }
    }
  }
}
```

---

## Variáveis de ambiente

| Variável | Descrição | Obrigatório | Padrão |
|---|---|---|---|
| `ZENDESK_EMAIL` | Email da conta Zendesk | ✅ | — |
| `ZENDESK_TOKEN` | API Token gerado no Admin Center | ✅ | — |
| `ZENDESK_SUBDOMAIN` | Subdomínio (ex: `empresa` de `empresa.zendesk.com`) | ✅ | — |
| `ZENDESK_TIMEOUT` | Timeout das chamadas HTTP em segundos | ❌ | `30` |
| `ZENDESK_MAX_RETRIES` | Número de tentativas em falhas transitórias | ❌ | `3` |
| `LOG_LEVEL` | Nível de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | ❌ | `INFO` |
| `ENVIRONMENT` | `development` habilita debug mode do FastMCP | ❌ | `production` |

Se qualquer variável obrigatória estiver ausente, o servidor encerra imediatamente com mensagem de erro clara — nenhuma ferramenta é registrada antes da validação passar.

---

## Ferramentas disponíveis

### Tickets

| Ferramenta | Descrição |
|---|---|
| `get_ticket` | Detalhes completos: assunto, status, prioridade, solicitante, responsável, organização, tags, CSAT, descrição |
| `get_ticket_comments` | Thread de comentários; use `include_internal=True` para incluir notas internas de agentes |
| `get_ticket_metrics` | Métricas SLA: primeiro tempo de resposta, tempo de resolução, reaberturas, total de respostas |
| `search_tickets` | Busca textual com sintaxe Zendesk (ex: `status:open assignee:me tag:billing`) |
| `list_tickets` | Tickets ordenados por última atualização, com filtro opcional por status |
| `get_ticket_audits` | Trilha de auditoria completa: criação, alterações de campo (`antigo → novo`), comentários |
| `get_linked_incidents` | Tickets de incidente vinculados a um ticket de problema |
| `get_tickets_count_by_status` | Resumo do dashboard: contagem por status + total geral |

### Usuários

| Ferramenta | Descrição |
|---|---|
| `get_user` | Detalhes do usuário com nome da organização resolvido, papel, tags, status |
| `search_users` | Busca usuários por nome, e-mail ou papel |

### Organizações

| Ferramenta | Descrição |
|---|---|
| `get_organization` | Detalhes da organização: domínios, tags, notas, grupo |
| `list_organizations` | Lista paginada de todas as organizações |

### Métricas

| Ferramenta | Descrição |
|---|---|
| `list_satisfaction_ratings` | Avaliações CSAT; filtre por `score="good"` ou `score="bad"` |

---

## Arquitetura

O servidor roda inteiramente na máquina local. Nenhum dado é enviado a terceiros além da API oficial do Zendesk.

```
Sua Máquina
┌─────────────────────────────────────────────────┐
│                                                 │
│  Cliente MCP (LLM / agente)                     │
│       ↕  stdio (comunicação local)              │
│  uvx zendesk-mcp-ro                             │
│       ↕  HTTPS (apenas API oficial Zendesk)     │
│  sua-empresa.zendesk.com/api/v2                 │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Desenvolvimento

```bash
git clone https://github.com/jonhnatta/zendesk-mcp-server.git
cd zendesk-mcp-server
uv sync
cp .env.example .env

make test        # 64 testes (100% offline, sem conta Zendesk)
make test-cov    # com relatório de cobertura
make lint        # ruff check + format --check
make typecheck   # mypy --strict
make dev-install # uv sync + pre-commit install
```

---

## Licença

MIT
