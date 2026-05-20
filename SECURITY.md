# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| latest | ✅ |

## Reporting a vulnerability

**Não abra uma issue pública para reportar vulnerabilidades de segurança.**

Use o [GitHub Security Advisory](https://github.com/jonhnatta/zendesk-mcp-server/security/advisories/new) para enviar um relatório privado. Inclua:

- Descrição da vulnerabilidade
- Passos para reproduzir
- Impacto potencial
- Sugestão de correção (opcional)

Você receberá uma resposta em até 72 horas. Se a vulnerabilidade for confirmada, uma correção será publicada o mais rápido possível com crédito ao responsável pelo reporte.

## Scope

Este servidor MCP é **somente leitura** — o `ZendeskClient` expõe apenas o método `get()`. Escrita de dados é arquiteturalmente impossível.

Ainda assim, são relevantes reportes sobre:
- Vazamento de credenciais (token Zendesk) em logs ou outputs
- Injeção via parâmetros de tools que afete a API do Zendesk
- Dependências com vulnerabilidades conhecidas
