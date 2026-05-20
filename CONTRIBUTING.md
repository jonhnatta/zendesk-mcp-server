# Contribuindo com o zendesk-mcp-server

Obrigado pelo interesse em contribuir! Este guia explica como configurar o ambiente, o padrão de commits e como adicionar novas tools.

---

## Setup do ambiente de desenvolvimento

```bash
git clone https://github.com/jonhnatta/zendesk-mcp-server.git
cd zendesk-mcp-server
uv sync
uv run pre-commit install
cp .env.example .env  # preencha com suas credenciais de teste
```

Comandos disponíveis:

```bash
make test        # roda os 64 testes (100% offline, sem conta Zendesk)
make test-cov    # testes com relatório de cobertura
make lint        # ruff check + format --check
make format      # ruff check --fix + format
make typecheck   # mypy --strict
```

---

## Como adicionar uma nova tool

### 1. Escolha o módulo correto

| Módulo | Caminho | Quando usar |
|---|---|---|
| Tickets | `src/zendesk_mcp_ro/tools/tickets.py` | Qualquer endpoint `/tickets` |
| Usuários | `src/zendesk_mcp_ro/tools/users.py` | Endpoints `/users` |
| Organizações | `src/zendesk_mcp_ro/tools/organizations.py` | Endpoints `/organizations` |
| Métricas | `src/zendesk_mcp_ro/tools/metrics.py` | Satisfação, SLA, relatórios |

Se a tool não se encaixa em nenhum módulo existente, crie um novo em `src/zendesk_mcp_ro/tools/` e registre-o em `server.py`.

### 2. Implemente a lógica de negócio em uma função privada

```python
async def _get_exemplo(client: ZendeskClient, exemplo_id: int) -> str:
    try:
        data = await client.get(f"/api/v2/exemplos/{exemplo_id}.json")
        e = data["exemplo"]
        return f"Exemplo #{e['id']}: {e['name']}"
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return f"Exemplo {exemplo_id} not found"
        raise
```

Regras:
- Funções `_get_*`: capturar `httpx.HTTPStatusError`, retornar string de erro em 404, re-raise nos demais
- Funções `_list_*` e `_search_*`: propagar todos os erros sem try/except
- Nunca escrever em `stdout` — use `logger` (stderr) se precisar de logging

### 3. Registre a tool via closure no `register()`

```python
def register(mcp: FastMCP, client: ZendeskClient) -> None:
    @mcp.tool()
    async def get_exemplo(exemplo_id: int) -> str:
        """Retorna os dados de um exemplo pelo ID.

        Args:
            exemplo_id: ID numérico do exemplo no Zendesk.

        Returns:
            Dados do exemplo formatados, ou mensagem de erro se não encontrado.
        """
        return await _get_exemplo(client, exemplo_id)
```

A docstring é obrigatória — ela é exibida ao LLM como descrição da ferramenta.

### 4. Escreva os testes

Crie ou edite o arquivo de testes correspondente em `tests/unit/`. Use `respx` para mockar as chamadas HTTP — nenhum teste deve bater na API real.

```python
import pytest
import respx
import httpx
from zendesk_mcp_ro.tools.exemplo import _get_exemplo


@pytest.mark.asyncio
async def test_get_exemplo_happy_path(mock_client):
    with respx.mock:
        respx.get("https://empresa.zendesk.com/api/v2/exemplos/1.json").mock(
            return_value=httpx.Response(200, json={"exemplo": {"id": 1, "name": "Teste"}})
        )
        result = await _get_exemplo(mock_client, 1)
    assert "Exemplo #1" in result
    assert "Teste" in result


@pytest.mark.asyncio
async def test_get_exemplo_not_found(mock_client):
    with respx.mock:
        respx.get("https://empresa.zendesk.com/api/v2/exemplos/99.json").mock(
            return_value=httpx.Response(404)
        )
        result = await _get_exemplo(mock_client, 99)
    assert result == "Exemplo 99 not found"
```

### 5. Verifique que tudo passa

```bash
make test
make lint
make typecheck
```

### 6. Abra um PR

Branch: `feat/<nome-da-tool>`
Título e descrição: em inglês

---

## Padrão de commits

Todos os commits devem ser **semânticos** e **atômicos**.

| Prefixo | Quando usar |
|---|---|
| `feat:` | Nova tool ou novo comportamento |
| `fix:` | Correção de bug |
| `test:` | Adicionar ou corrigir testes sem mudar produção |
| `refactor:` | Mudança interna sem alterar comportamento externo |
| `docs:` | README, docstrings, comentários |
| `chore:` | Dependências, configs, CI |

Um commit = uma mudança lógica. Se não cabe em uma linha sem usar "e", quebre em dois commits.

---

## Pull Requests

- Títulos e descrições em inglês
- Um PR por feature
- Todos os checks (lint, typecheck, tests) devem passar antes do merge
- Descreva o que muda e por quê, não como
