# Publicações – Advocacia Soares

Publica automaticamente no Instagram (@soaresadvc) e na Página do Facebook os
posts **aprovados** na aba **PUBLICAÇÕES** da planilha VISÃO GERAL - JASA.

## Como funciona

1. Conteúdos entram na pasta do Drive `PUBLICAÇÕES INSTA E FACE / 01 ENTRADA`.
2. A rotina semanal do Claude cria os posts (arte + legenda), salva as artes em
   `02 POSTS GERADOS` e inclui uma linha por post na aba PUBLICAÇÕES.
3. O Jailson revisa e marca **APROVAR = Sim** (pode mudar data, hora e legenda).
4. Este repositório roda de hora em hora (`.github/workflows/publicar.yml`):
   lê a planilha `FILA APROVADA` (que só mostra os aprovados), publica o que já
   chegou na data/hora e grava o resultado em `status.csv`, que aparece na
   coluna STATUS da aba.

Para publicar na hora: aba **Actions → Publicar posts aprovados → Run workflow**.

## Configuração

Settings → Secrets and variables → Actions

| Tipo | Nome | O que é |
|---|---|---|
| Secret | `META_TOKEN` | token do app "Soares Advocacia Publicacoes" (nunca colar em outro lugar) |
| Variable | `FILA_ID` | ID da planilha FILA APROVADA |
| Variable | `IG_USER_ID` | ID da conta do Instagram |
| Variable | `FB_PAGE_ID` | ID da Página do Facebook |

Sem `META_TOKEN`, roda em **modo simulação** (não publica, só testa a fila e as artes).

## Pastas

- `publicar.py` – publicador
- `gerador/` – modelos de arte (identidade visual) e renderizador usados pela rotina semanal
- `midia/` – imagens já publicadas (precisam de endereço público para a Meta buscar)
- `status.csv` – registro de cada publicação
