# Rotina semanal de criação de posts – Advocacia Soares

Executada todo domingo pelo Claude (tarefa agendada). Também serve de guia para
pedidos avulsos ("faz um story sobre...").

## Onde fica cada coisa
- Planilha: VISÃO GERAL - JASA – `1EWl4M45oD3UbPBsDdoY-8jIS3own-YmZ_ObeFQcF2hI`, aba **PUBLICAÇÕES**
  (colunas A–N: ID, DATA, HORA, TIPO, DESTINO, TEMA, FONTE, LEGENDA, PRÉVIA, ARQUIVOS, ALERTA OAB, APROVAR, OBSERVAÇÕES DO JAILSON, STATUS).
  Nunca escrever nas colunas L (APROVAR), M (OBSERVAÇÕES) e N (STATUS – fórmula). Nunca mexer nas outras abas.
- Pasta Drive "PUBLICAÇÕES INSTA E FACE": `1yKURaCA8fzDLRouonCErZhajR1UopL7E`
  - 01 ENTRADA (conteúdos do Jailson): `1-JgH250kHm79L7L6EIxA0tp4lKrCIgIA`
  - 02 POSTS GERADOS (artes): `1hxTm78KqqtNiFHfhcPy1GCnt7RF36fZ3`
- Renderizador: `gerador/render.py` deste repositório (público: `git clone https://github.com/jailson-rgb/publicacoes-soares`).

## Grade da semana seguinte (horário de Brasília)
- Story: segunda a sexta, 09:00 (indicador do mês, "você sabia?", chamada para o post do feed).
- Carrossel de jurisprudência (STJ/STF): terça, 11:00.
- Carrossel com conteúdo do Jailson (pasta ENTRADA): quinta, 11:00. Sem conteúdo novo → tema educativo de recuperação de crédito.
- DESTINO padrão: "Instagram + Facebook".

## Fontes
1. Pasta 01 ENTRADA – arquivos novos desde a última rotina (o que já virou post fica registrado na coluna TEMA/FONTE).
2. Informativo de Jurisprudência do STJ (scon.stj.jus.br/jurisprudencia/externo/informativo/) e Informativo STF (semanal).
   Filtrar: Direito Empresarial; Direito Civil e Processual Civil quando tratar de recuperação de crédito, cobrança,
   execução, títulos de crédito, fraude à execução/contra credores, desconsideração da personalidade jurídica,
   recuperação judicial e falência.
3. Indicadores: Serasa Experian (inadimplência das empresas, falências e recuperações judiciais) e Banco Central
   (Estatísticas Monetárias e de Crédito – inadimplência PJ). Sempre citar fonte e mês de referência.

## Regras de conteúdo (Provimento 205/2021 da OAB) – obrigatórias
- Caráter informativo e educativo, linguagem para empresário (sem juridiquês), tom sóbrio.
- PROIBIDO: casos concretos do escritório (mesmo anonimizados), resultados obtidos ("conseguimos", "recuperamos"),
  promessa de resultado, nomes de clientes/partes, números de processo do escritório, chamada de venda direta,
  ostentação, comparação com outros escritórios.
- Decisões dos próprios casos só podem inspirar posts em forma de TESE genérica ("o tribunal pode bloquear bens
  quando..."), sem indicar que o caso é do escritório.
- Decisões de tribunais superiores (STJ/STF) podem ser citadas com referência oficial (número do recurso/informativo).
- Na dúvida, preencher a coluna K (ALERTA OAB) explicando o ponto, para o Jailson revisar.
- Nunca inventar decisão, número de processo ou estatística: tudo precisa ter fonte verificável.

## Formato dos posts
- Carrossel: 4 a 7 lâminas – capa (`capa`), conteúdo (`decisao`/`topico`), fechamento (`fechamento`).
- Story: 1 lâmina (`story` ou `story_numero`).
- Legenda: 600–1.200 caracteres, parágrafos curtos, 3–6 hashtags (#direitoempresarial #recuperacaodecredito ...),
  terminar com "Advocacia Soares · Direito Empresarial · Crédito e Patrimônio". Sem promessa e sem "fale conosco agora".

## Passo a passo
1. Ler a aba PUBLICAÇÕES para ver o último ID (formato P2026-NNN) e o que já foi feito.
2. Reunir o material das fontes e escolher os temas da semana.
3. Para cada post, escrever o JSON (ver `gerador/exemplo-*.json`) e renderizar com
   `python gerador/render.py post.json saida/` (instalar `playwright` e o navegador se necessário).
4. Enviar os PNG para "02 POSTS GERADOS" com nome `<ID>-01.png`, `<ID>-02.png`...
5. Acrescentar uma linha por post na aba PUBLICAÇÕES (A–K): ID; DATA (dd/mm/aaaa); HORA (hh:mm); TIPO; DESTINO; TEMA;
   FONTE; LEGENDA; PRÉVIA = link da primeira imagem; ARQUIVOS = IDs dos arquivos no Drive separados por vírgula, na ordem;
   ALERTA OAB (vazio se não houver dúvida).
6. Terminar com um resumo curto para o Jailson: quantos posts, datas, e quais têm alerta.
