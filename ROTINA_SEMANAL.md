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
- Story: segunda às 12:00; terça a sexta às 09:00 (indicador do mês, "você sabia?", chamada para o post do feed).
  (O Jailson costuma aprovar na segunda de manhã; por isso o story de segunda sai ao meio-dia.)
- Carrossel de jurisprudência (STJ/STF): terça, 12:00.
- Carrossel com conteúdo do Jailson (pasta ENTRADA): quinta, 12:00. Sem conteúdo novo → tema educativo de direito empresarial ou recuperação de ativos.
- DESTINO padrão: "Instagram + Facebook".
- Aprovação: o Jailson marca APROVAR = Sim linha a linha OU digita uma data na célula P1 da aba PUBLICAÇÕES
  ("APROVAR TUDO ATÉ"): todas as linhas até essa data com APROVAR em branco ficam aprovadas; "Não" e "Ajustar"
  continuam bloqueadas. A rotina nunca escreve em P1.

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

## Sigilo do know-how do escritório – obrigatório
- NUNCA revelar COMO o escritório trabalha: métodos de investigação/pesquisa patrimonial, fontes, sistemas,
  ferramentas, ordem das medidas, estratégias processuais específicas, provas produzidas ou como foram obtidas.
- Conteúdo educativo fala do QUE a lei permite e do QUE os tribunais decidem (o direito), nunca do passo a passo
  operacional do escritório. Ex.: pode "a venda de bens para fugir da execução pode ser anulada"; não pode
  "veja como descobrimos que o devedor escondeu bens".
- Quando houver menção a solução obtida, usar fórmula genérica ("solucionado pelos meios jurídicos cabíveis"),
  sem detalhar provas, diligências ou estratégia.
- Nunca inventar decisão, número de processo ou estatística: tudo precisa ter fonte verificável.

## Trends (aprovado pelo Jailson em 14/11/2026)
Filtro obrigatório – a trend só entra se TODAS forem verdadeiras:
- conversa com dono/gestor de indústria, distribuidor ou atacadista;
- dá para ligar a direito empresarial ou recuperação de ativos;
- tom sóbrio (Provimento 205): nada de dança, humor exagerado, exposição pessoal, ostentação, cliente, caso ou resultado;
- respeita o sigilo do know-how (seção acima).
Se nada da semana passar no filtro, não sai trend naquela semana (registrar isso no resumo final).

1. Trend de ASSUNTO – toda semana:
   - Pesquisar (busca na web/notícias da semana) o tema mais comentado que afete empresas: datas do varejo, caixa e 13º,
     reforma tributária, recuperação judicial de empresa conhecida, golpes contra empresas, mudanças de lei etc.
   - Virar 1 story (09:00 de um dia útil, no lugar de um story comum) ou 1 carrossel extra (quarta, 12:00) se o tema render.
   - FONTE = "Trend de assunto" + link da fonte na coluna TEMA.
2. Trend de FORMATO (Reels) – a cada 15 dias (semanas pares do ano: rodar quando o nº da semana ISO for par):
   - Pesquisar os formatos de Reels em alta na semana (POV, "3 erros que…", "ninguém te conta que…", texto na tela
     sincronizado com áudio do momento) e adaptar a um tema jurídico do escritório.
   - Gerar o vídeo vertical 1080x1920 (8–15 s) só com texto na tela no padrão da marca (ffmpeg sobre as lâminas `story`),
     SEM áudio, e enviar para "02 POSTS GERADOS".
   - Linha na planilha com TIPO = "Reels", horário sugerido (sexta 12:00) e, na LEGENDA, primeiro a legenda e depois
     a linha "ÁUDIO SUGERIDO: <nome do áudio/trend>". O publicador NÃO publica Reels (fica com status "Manual"):
     o Jailson abre o vídeo no app, coloca o áudio indicado e publica.

## Terminologia (pedido do Jailson)
- Usar "recuperação de ATIVOS", não "recuperação de crédito". "Crédito" só como termo técnico (habilitação de créditos,
  título de crédito) ou na assinatura da marca "Crédito e Patrimônio".
- Destaques do Instagram: não acrescentar stories a destaques sem pedido do Jailson (isso muda a ordem deles).

## Formato dos posts
- Carrossel: 4 a 7 lâminas – capa (`capa`), conteúdo (`decisao`/`topico`), fechamento (`fechamento`).
- Story: 1 lâmina (`story` ou `story_numero`).
- Legenda: 600–1.200 caracteres, parágrafos curtos, 3–6 hashtags (#direitoempresarial #recuperacaodeativos ...),
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

## LinkedIn
- REGRA (Jailson, 15/11/2026): toda publicação do LinkedIn é feita NA PÁGINA "Advocacia Soares"
  (linkedin.com/company/advocacia-soares) e depois COMPARTILHADA no perfil pessoal do Jailson
  ("Compartilhar com ideias", com uma frase curta dele). Nunca publicar só no perfil pessoal.
- Sempre com legenda (texto + hashtags); publicação sem texto quase não aparece no feed.
- Carrossel no LinkedIn = documento PDF (as mesmas lâminas do Instagram).
- Post técnico semanal na Página Advocacia Soares (texto corrido, 1.500–3.000 caracteres, tom técnico),
  compartilhado no perfil pessoal. Autoria: marcar o colaborador no texto ("por ...").
- Artigo mensal "caso de fundo": inspirado em caso real do escritório, escrito como SITUAÇÃO ILUSTRATIVA
  ("Imagine uma indústria que vende a prazo a um distribuidor que, cobrado, transfere seus bens..."), nunca como
  "nosso caso". Estrutura: 1) a situação; 2) o problema jurídico; 3) o que diz a lei e a jurisprudência pública
  (STJ/STF/TJRS, com referência); 4) lições práticas para o empresário; 5) fecho institucional sóbrio.
  Proibido: partes, número do processo, valores, cidade, datas, detalhes que identifiquem; "conseguimos/vencemos";
  qualquer detalhe de método, prova ou estratégia (ver Sigilo do know-how). No máximo citar o tribunal de forma genérica.
  Todo artigo entra na planilha com ALERTA OAB preenchido para revisão do Jailson.
