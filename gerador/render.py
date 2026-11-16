"""
Renderizador de artes da Advocacia Soares (identidade "Colunas", Montserrat).

Uso:  python gerador/render.py post.json pasta_saida/
O JSON descreve um post:
{
  "id": "P2026-001",
  "tipo": "Carrossel" | "Story" | "Post único",
  "tema": "Recuperação de ativos",          # etiqueta no topo da capa
  "laminas": [
    {"layout": "capa",    "titulo": "...", "subtitulo": "..."},
    {"layout": "topico",  "numero": "1", "titulo": "...", "texto": "..."},
    {"layout": "decisao", "tribunal": "STJ", "referencia": "REsp 0.000.000/RS · Informativo 900",
                          "titulo": "...", "texto": "..."},
    {"layout": "fechamento", "titulo": "...", "texto": "..."},
    {"layout": "story",   "chamada": "Você sabia?", "titulo": "...", "texto": "..."},
    {"layout": "story_numero", "numero": "9,3 mi", "titulo": "...", "fonte": "Serasa Experian, ago/2026"},
    # LAYOUTS EXTRAS (feed 1080x1350): post único ou carrosséis variados. "fundo": escuro | claro | medio
    {"layout": "frase", "frase": "...", "assinatura": "...", "fundo": "escuro"},
    {"layout": "dado", "chamada": "...", "numero": "9,3 mi", "titulo": "...", "texto": "...", "fonte": "... (mês/ano)"},
    {"layout": "mito", "mito": "...", "verdade": "..."},
    {"layout": "comparativo", "titulo": "...", "esquerda": "...", "itens_esquerda": [...], "direita": "...", "itens_direita": [...]},
    {"layout": "checklist", "titulo": "...", "itens": ["...", "..."]},
    {"layout": "passos", "titulo": "...", "passos": [{"titulo": "...", "texto": "..."}]},
    {"layout": "pergunta", "chamada": "...", "pergunta": "...", "resposta": "..."},
    {"layout": "barras", "chamada": "...", "titulo": "...", "dados": [{"rotulo": "jun", "valor": 8.9, "texto": "8,9 mi"}], "fonte": "..."},
    {"layout": "nota", "data": "...", "titulo": "...", "texto": "...", "assinatura": "Jailson Soares"}
  ]
}
PEÇAS LARGAS (em vez de "laminas", usar "largo"; desenha uma arte larga e corta):
  {"largo": {"layout": "mosaico", "chamada": "...", "titulo": "...", "texto": "...", "rodapes": ["...", "...", "..."], "fundo": "escuro|claro"}}
     -> 01 (esquerda), 02 (meio), 03 (direita): 3 posts que formam uma imagem na grade do perfil.
  {"largo": {"layout": "jornada", "tema": "...", "titulo": "...", "subtitulo": "...", "passos": [{"titulo": "...", "texto": "..."}]}}
     -> carrossel panorâmico contínuo (capa + 1 lâmina por etapa).
NOVOS (16/11/2026): foto, foto_fundo, jurisprudencia, glossario, serie, split, palavra, linha_tempo, grade, marcatexto, fluxo, moldura, ranking (ver gerador/exemplos/exemplo-novos-16-11.json).
Não há layout de "resultado"/placar: o Provimento 205/2021 da OAB proíbe divulgar resultados.
Gera 01.png, 02.png... (1080x1350 no feed, 1080x1920 no story).
"""
import html
import json
import os
import sys

from playwright.sync_api import sync_playwright

AQUI = os.path.dirname(os.path.abspath(__file__))
DARK, GOLD, GOLDD, CREAM, LIGHT, INK, MUTED = "#1F3A3D", "#C29A5B", "#8C6A3A", "#F7F5F0", "#F4F1EA", "#1C2B2C", "#4A5A5B"
F = "font-family: Montserrat, sans-serif"


def e(t):
    return html.escape(str(t or "")).replace("\n", "<br>")


def mark(px, c=LIGHT, g=GOLD):
    return (f'<svg width="{px}" height="{px}" viewBox="0 0 120 120"><rect x="8" y="54" width="26" height="60" fill="{c}"></rect>'
            f'<rect x="47" y="32" width="26" height="82" fill="{c}"></rect><rect x="86" y="8" width="26" height="106" fill="{g}"></rect></svg>')


def horiz(s=1.0, c=LIGHT, g=GOLD):
    return (f'<div style="display:flex;align-items:center;gap:{round(22*s)}px">{mark(round(92*s), c, g)}'
            f'<div style="display:flex;flex-direction:column;gap:{max(1, round(2*s))}px">'
            f'<p style="margin:0;font-size:{round(30*s)}px;font-weight:300;line-height:1.1;color:{c}">Advocacia</p>'
            f'<p style="margin:0;font-size:{round(48*s)}px;font-weight:700;letter-spacing:-0.5px;line-height:1;color:{g}">Soares</p></div></div>')


def selo(c=LIGHT, g=GOLD):
    return f'<div style="display:flex;align-items:center;gap:16px">{mark(56, c, g)}<p style="margin:0;font-size:28px;font-weight:600;color:{c}">@soaresadvc</p></div>'


def assinatura(c1, c2, size=18):
    return (f'<div style="display:flex;flex-direction:column;align-items:flex-end;gap:5px">'
            f'<p style="margin:0;font-size:{size}px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{c1}">Direito Empresarial</p>'
            f'<p style="margin:0;font-size:{size}px;font-weight:600;letter-spacing:2px;text-transform:uppercase;color:{c2}">Crédito e Patrimônio</p></div>')


def contador(n, total, c, g):
    return f'<p style="margin:0;font-size:34px;font-weight:300;color:{c}"><span style="font-weight:700;color:{g}">{n:02d}</span> / {total:02d}</p>'


def seta(c, g):
    return (f'<div style="display:flex;align-items:center;gap:14px"><p style="margin:0;font-size:28px;font-weight:600;color:{c}">Arraste</p>'
            f'<svg width="56" height="28" viewBox="0 0 40 20"><path d="M2 10 H36 M28 3 L36 10 L28 17" fill="none" stroke="{g}" stroke-width="3"></path></svg></div>')


def caixa(bg, corpo, w=1080, h=1350, pad="88px"):
    return f'<div style="width:{w}px;height:{h}px;background:{bg};padding:{pad};box-sizing:border-box;display:flex;flex-direction:column;justify-content:space-between">{corpo}</div>'


def rodape_claro():
    return (f'<div style="display:flex;flex-direction:column;gap:22px"><div style="height:2px;background:{GOLDD}"></div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center">{horiz(0.55, DARK, GOLDD)}{assinatura(DARK, GOLDD)}</div></div>')


def lam_capa(l, n, total, tema):
    topo = (f'<div style="display:flex;justify-content:space-between;align-items:center">{selo()}'
            f'<p style="margin:0;padding:12px 26px;border:2px solid {GOLD};border-radius:999px;font-size:19px;font-weight:600;letter-spacing:3px;text-transform:uppercase;color:{GOLD}">{e(tema)}</p></div>')
    meio = (f'<div style="display:flex;flex-direction:column;gap:36px"><div style="width:120px;height:6px;background:{GOLD}"></div>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 92)}px;font-weight:700;line-height:1.06;letter-spacing:-2px;color:{LIGHT}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:0;font-size:42px;font-weight:400;line-height:1.3;color:#D9D2C3">{e(l.get("subtitulo"))}</p></div>')
    base = f'<div style="display:flex;justify-content:space-between;align-items:center">{contador(n, total, LIGHT, GOLD) if total > 1 else "<span></span>"}{seta(LIGHT, GOLD) if total > 1 else ""}</div>'
    return caixa(DARK, topo + meio + base)


def lam_topico(l, n, total, tema):
    topo = f'<div style="display:flex;justify-content:flex-end">{contador(n, total, INK, GOLDD)}</div>'
    num = f'<p style="margin:0;font-size:190px;font-weight:700;line-height:0.9;color:{GOLDD}">{e(l.get("numero"))}</p>' if l.get("numero") else ""
    meio = (f'<div style="display:flex;flex-direction:column;gap:30px">{num}'
            f'<p style="margin:0;font-size:{l.get("tamanho", 66)}px;font-weight:700;line-height:1.1;letter-spacing:-1.5px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:0;font-size:36px;font-weight:400;line-height:1.45;color:{INK}">{e(l.get("texto"))}</p></div>')
    return caixa(CREAM, topo + meio + rodape_claro())


def lam_decisao(l, n, total, tema):
    topo = (f'<div style="display:flex;justify-content:space-between;align-items:center">'
            f'<p style="margin:0;padding:10px 24px;background:{DARK};border-radius:999px;font-size:22px;font-weight:700;letter-spacing:3px;color:{GOLD}">DECISÃO DO {e(l.get("tribunal", "STJ"))}</p>'
            f'{contador(n, total, INK, GOLDD) if total > 1 else ""}</div>')
    meio = (f'<div style="display:flex;flex-direction:column;gap:28px">'
            f'<p style="margin:0;font-size:{l.get("tamanho", 60)}px;font-weight:700;line-height:1.12;letter-spacing:-1.2px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:0;font-size:34px;font-weight:400;line-height:1.45;color:{INK}">{e(l.get("texto"))}</p>'
            f'<p style="margin:0;font-size:22px;font-weight:500;color:{MUTED}">{e(l.get("referencia"))}</p></div>')
    return caixa(CREAM, topo + meio + rodape_claro())


def lam_fechamento(l, n, total, tema):
    meio = (f'<div style="display:flex;flex-direction:column;gap:34px"><div style="width:120px;height:6px;background:{GOLD}"></div>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 72)}px;font-weight:700;line-height:1.1;letter-spacing:-1.5px;color:{LIGHT}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:0;font-size:36px;font-weight:400;line-height:1.45;color:#D9D2C3">{e(l.get("texto"))}</p></div>')
    base = f'<div style="display:flex;justify-content:space-between;align-items:flex-end">{horiz(0.75)}{assinatura(LIGHT, GOLD)}</div>'
    topo = f'<div style="display:flex;justify-content:flex-end">{contador(n, total, LIGHT, GOLD) if total > 1 else ""}</div>'
    return caixa(DARK, topo + meio + base)


def lam_story(l, n, total, tema):
    meio = (f'<div style="display:flex;flex-direction:column;gap:44px"><p style="margin:0;font-size:30px;font-weight:600;letter-spacing:5px;text-transform:uppercase;color:{GOLD}">{e(l.get("chamada", "Você sabia?"))}</p>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 82)}px;font-weight:700;line-height:1.12;letter-spacing:-1.5px;color:{LIGHT}">{e(l.get("titulo"))}</p>'
            f'<div style="width:140px;height:6px;background:{GOLD}"></div><p style="margin:0;font-size:40px;font-weight:400;line-height:1.4;color:#D9D2C3">{e(l.get("texto"))}</p></div>')
    base = f'<div style="display:flex;justify-content:space-between;align-items:flex-end">{horiz(0.8)}{assinatura(LIGHT, GOLD, 17)}</div>'
    return caixa(DARK, selo() + meio + base, 1080, 1920, "140px 96px")


def lam_story_numero(l, n, total, tema):
    meio = (f'<div style="display:flex;flex-direction:column;gap:30px"><p style="margin:0;font-size:30px;font-weight:600;letter-spacing:5px;text-transform:uppercase;color:{GOLD}">{e(l.get("chamada", "Número do mês"))}</p>'
            f'<p style="margin:0;font-size:220px;font-weight:700;line-height:1;letter-spacing:-6px;color:{GOLD}">{e(l.get("numero"))}</p>'
            f'<p style="margin:0;font-size:60px;font-weight:700;line-height:1.15;color:{LIGHT}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:0;font-size:26px;font-weight:500;color:#AEBBB8">Fonte: {e(l.get("fonte"))}</p></div>')
    base = f'<div style="display:flex;justify-content:space-between;align-items:flex-end">{horiz(0.8)}{assinatura(LIGHT, GOLD, 17)}</div>'
    return caixa(DARK, selo() + meio + base, 1080, 1920, "140px 96px")


LAYOUTS = {"capa": lam_capa, "topico": lam_topico, "decisao": lam_decisao, "fechamento": lam_fechamento,
           "story": lam_story, "story_numero": lam_story_numero}


# ------------------------------------------------------------------ layouts extras (feed 1080x1350)
# Servem para POST ÚNICO (uma lâmina só) e para compor carrosséis com estruturas diferentes.
# Vários aceitam "fundo": "escuro" (verde da marca) | "claro" (creme) | "medio" (areia).
# Na Soares NÃO existe layout de resultado/placar (Provimento 205/2021 proíbe divulgar resultados).
SAND, LINHA = "#E8DFCC", "#C9BFA9"


def cores(l, padrao):
    f = l.get("fundo", padrao)
    if f == "escuro":
        return DARK, LIGHT, GOLD, True
    if f == "medio":
        return SAND, INK, GOLDD, False
    return CREAM, INK, GOLDD, False


def abs_caixa(bg, corpo, w=1080, h=1350):
    return f'<div style="width:{w}px;height:{h}px;background:{bg};position:relative;overflow:hidden;{F}">{corpo}</div>'


def marca_fundo(escuro, right=-150, top=330, px=1050):
    op = 0.07 if escuro else 0.05
    c = LIGHT if escuro else DARK
    return f'<div style="position:absolute;right:{right}px;top:{top}px;opacity:{op}">{mark(px, c, c)}</div>'


def topo_feed(n, total, escuro):
    c, g = (LIGHT, GOLD) if escuro else (DARK, GOLDD)
    cont = contador(n, total, c, g) if total > 1 else ""
    return f'<div style="display:flex;justify-content:space-between;align-items:center">{horiz(0.55, c, g)}{cont}</div>'


def base_feed(escuro):
    c, g = (LIGHT, GOLD) if escuro else (DARK, GOLDD)
    linha = "rgba(244,241,234,.35)" if escuro else LINHA
    return (f'<div style="display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid {linha};padding-top:22px">'
            f'<p style="margin:0;font-size:22px;font-weight:500;color:{c};opacity:.8">advocaciasoares.com · OAB/RS 115.168</p>'
            f'{assinatura(c, g, 16)}</div>')


def moldura(bg, escuro, n, total, meio, extra="", escuro_topo=None):
    et = escuro if escuro_topo is None else escuro_topo
    return abs_caixa(bg, extra +
                     '<div style="position:absolute;inset:88px;display:flex;flex-direction:column;justify-content:space-between">'
                     + topo_feed(n, total, et) + meio + base_feed(escuro) + '</div>')


def l_frase(l, n, total, tema=""):
    bg, txt, dest, esc = cores(l, "escuro")
    meio = (f'<div><p style="margin:0;height:150px;font-size:260px;font-weight:700;line-height:1;color:{dest}">“</p>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 76)}px;font-weight:700;line-height:1.12;letter-spacing:-1.5px;color:{txt}">{e(l.get("frase"))}</p>'
            f'<p style="margin:40px 0 0;font-size:26px;letter-spacing:4px;font-weight:600;text-transform:uppercase;color:{dest}">{e(l.get("assinatura", ""))}</p></div>')
    return moldura(bg, esc, n, total, meio, marca_fundo(esc))


def l_dado(l, n, total, tema=""):
    bg, txt, dest, esc = cores(l, "claro")
    fonte = ("Fonte: " + e(l["fonte"])) if l.get("fonte") else ""
    meio = (f'<div style="text-align:center">'
            f'<p style="margin:0 0 20px;font-size:26px;font-weight:700;letter-spacing:6px;text-transform:uppercase;color:{dest}">{e(l.get("chamada", ""))}</p>'
            f'<p style="margin:0;white-space:nowrap;font-size:{l.get("tamanho", 200)}px;font-weight:700;line-height:1;letter-spacing:-6px;color:{GOLD if esc else DARK}">{e(l.get("numero"))}</p>'
            f'<p style="margin:30px auto 0;max-width:820px;font-size:48px;font-weight:700;line-height:1.15;color:{txt}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:22px auto 0;max-width:800px;font-size:32px;line-height:1.42;color:{txt}">{e(l.get("texto"))}</p>'
            f'<p style="margin:26px 0 0;font-size:22px;font-weight:500;color:{txt};opacity:.7">{fonte}</p></div>')
    return moldura(bg, esc, n, total, meio)


def l_mito(l, n, total, tema=""):
    faixa = f'<div style="position:absolute;left:0;right:0;top:0;height:660px;background:{DARK}"></div>'
    meio = (f'<div style="display:flex;flex-direction:column;flex:1;justify-content:space-between;margin:30px 0 40px">'
            f'<div style="height:420px;display:flex;flex-direction:column;justify-content:center">'
            f'<p style="margin:0 0 18px;font-size:28px;font-weight:700;letter-spacing:8px;color:{GOLD}">MITO</p>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 54)}px;font-weight:700;line-height:1.15;color:{LIGHT};text-decoration:line-through;text-decoration-color:{GOLD};text-decoration-thickness:4px">{e(l.get("mito"))}</p></div>'
            f'<div style="height:360px;display:flex;flex-direction:column;justify-content:center">'
            f'<p style="margin:0 0 18px;font-size:28px;font-weight:700;letter-spacing:8px;color:{GOLDD}">VERDADE</p>'
            f'<p style="margin:0;font-size:38px;line-height:1.42;color:{INK}">{e(l.get("verdade"))}</p></div></div>')
    return moldura(CREAM, False, n, total, meio, faixa, escuro_topo=True)


def l_comparativo(l, n, total, tema=""):
    def col(t, itens, cor, bg, tc):
        li = "".join(f'<p style="margin:0;font-size:30px;line-height:1.38;color:{tc}">{e(i)}</p>' for i in itens)
        return (f'<div style="flex:1;background:{bg};border-radius:22px;padding:40px 34px;display:flex;flex-direction:column;gap:24px">'
                f'<p style="margin:0;font-size:26px;font-weight:700;letter-spacing:3px;text-transform:uppercase;color:{cor}">{e(t)}</p>'
                f'<div style="height:4px;background:{cor};width:80px"></div>{li}</div>')
    esq = col(l.get("esquerda", ""), l.get("itens_esquerda", []), MUTED, "#fff", INK)
    dir_ = col(l.get("direita", ""), l.get("itens_direita", []), GOLD, DARK, LIGHT)
    meio = (f'<div><p style="margin:0 0 44px;font-size:{l.get("tamanho", 58)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<div style="display:flex;gap:26px">{esq}{dir_}</div></div>')
    return moldura(CREAM, False, n, total, meio)


def l_checklist(l, n, total, tema=""):
    bg, txt, dest, esc = cores(l, "claro")
    circ, marca, tit = (GOLD, DARK, LIGHT) if esc else (DARK, GOLD, DARK)
    itens = "".join(
        f'<div style="display:flex;gap:28px;align-items:flex-start"><div style="flex:none;width:62px;height:62px;border-radius:50%;'
        f'background:{circ};color:{marca};font-size:36px;font-weight:700;display:flex;align-items:center;justify-content:center">✓</div>'
        f'<p style="margin:6px 0 0;font-size:37px;line-height:1.32;color:{txt}">{e(i)}</p></div>' for i in l.get("itens", []))
    meio = (f'<div><p style="margin:0 0 50px;font-size:{l.get("tamanho", 60)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{tit}">{e(l.get("titulo"))}</p>'
            f'<div style="display:flex;flex-direction:column;gap:36px">{itens}</div></div>')
    return moldura(bg, esc, n, total, meio, marca_fundo(esc))


def l_passos(l, n, total, tema=""):
    ps = l.get("passos", [])
    blocos = []
    for i, p in enumerate(ps, 1):
        linha = f'<div style="width:4px;flex:1;background:{LINHA};min-height:40px"></div>' if i < len(ps) else ""
        blocos.append(
            f'<div style="display:flex;gap:34px"><div style="flex:none;display:flex;flex-direction:column;align-items:center">'
            f'<div style="width:76px;height:76px;border-radius:50%;background:{DARK};font-size:38px;font-weight:700;'
            f'color:{GOLD};display:flex;align-items:center;justify-content:center">{i}</div>{linha}</div>'
            f'<div style="padding-bottom:32px"><p style="margin:14px 0 0;font-size:38px;font-weight:700;color:{DARK}">{e(p.get("titulo"))}</p>'
            f'<p style="margin:10px 0 0;font-size:30px;line-height:1.42;color:{INK}">{e(p.get("texto"))}</p></div></div>')
    meio = (f'<div><p style="margin:0 0 46px;font-size:{l.get("tamanho", 58)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'{"".join(blocos)}</div>')
    return moldura(CREAM, False, n, total, meio)


def l_pergunta(l, n, total, tema=""):
    bg, txt, dest, esc = cores(l, "claro")
    interrog = GOLD if esc else SAND
    perg = LIGHT if esc else DARK
    q = f'<div style="position:absolute;right:60px;top:150px;font-size:760px;font-weight:700;line-height:1;color:{interrog};opacity:{.25 if esc else .9}">?</div>'
    meio = (f'<div style="position:relative"><p style="margin:0 0 26px;font-size:26px;font-weight:700;letter-spacing:6px;text-transform:uppercase;color:{dest}">{e(l.get("chamada", "Pergunta de empresário"))}</p>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 70)}px;font-weight:700;line-height:1.1;letter-spacing:-1.5px;color:{perg}">{e(l.get("pergunta"))}</p>'
            f'<div style="width:120px;height:6px;background:{GOLD};margin:42px 0"></div>'
            f'<p style="margin:0;font-size:37px;line-height:1.44;color:{txt}">{e(l.get("resposta"))}</p></div>')
    return moldura(bg, esc, n, total, meio, q)


def l_barras(l, n, total, tema=""):
    dados = l.get("dados", [])  # [{"rotulo": "jun", "valor": 8.9, "texto": "8,9 mi"}] – o último fica destacado
    mx = max([d["valor"] for d in dados] or [1])
    col = []
    for i, d in enumerate(dados):
        ult = i == len(dados) - 1
        alt = max(6, 100 * d["valor"] / mx)
        col.append(
            f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;gap:14px;height:100%">'
            f'<p style="margin:0;font-size:27px;font-weight:700;color:{GOLDD if ult else INK}">{e(d.get("texto", d["valor"]))}</p>'
            f'<div style="width:100%;height:{alt:.1f}%;background:{GOLD if ult else DARK};border-radius:12px 12px 0 0"></div>'
            f'<p style="margin:0;font-size:25px;color:{INK}">{e(d.get("rotulo"))}</p></div>')
    fonte = ("Fonte: " + e(l["fonte"])) if l.get("fonte") else ""
    meio = (f'<div><p style="margin:0 0 14px;font-size:26px;font-weight:700;letter-spacing:6px;text-transform:uppercase;color:{GOLDD}">{e(l.get("chamada", ""))}</p>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 56)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<div style="display:flex;gap:22px;height:480px;margin-top:50px;border-bottom:3px solid {INK}">{"".join(col)}</div>'
            f'<p style="margin:24px 0 0;font-size:22px;font-weight:500;color:{MUTED}">{fonte}</p></div>')
    return moldura(CREAM, False, n, total, meio)


def l_nota(l, n, total, tema=""):
    """Post estilo 'anotação' (cartão branco com sombra)."""
    meio = (f'<div style="background:#fff;border-radius:30px;box-shadow:0 18px 50px rgba(31,58,61,.14);padding:54px 56px 60px">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:34px">'
            f'<div style="display:flex;gap:8px;align-items:flex-end"><span style="width:14px;height:22px;background:{DARK}"></span>'
            f'<span style="width:14px;height:32px;background:{DARK}"></span><span style="width:14px;height:44px;background:{GOLD}"></span></div>'
            f'<p style="margin:0;font-size:24px;color:{MUTED}">{e(l.get("data", ""))}</p></div>'
            f'<p style="margin:0 0 26px;font-size:{l.get("tamanho", 50)}px;font-weight:700;line-height:1.15;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<p style="margin:0;font-size:35px;line-height:1.5;color:{INK}">{e(l.get("texto"))}</p>'
            f'<p style="margin:34px 0 0;font-size:28px;font-weight:600;color:{GOLDD}">— {e(l.get("assinatura", "Jailson Soares"))}</p></div>')
    return moldura(SAND, False, n, total, meio)


LAYOUTS.update({"frase": l_frase, "dado": l_dado, "mito": l_mito, "comparativo": l_comparativo, "checklist": l_checklist,
                "passos": l_passos, "pergunta": l_pergunta, "barras": l_barras, "nota": l_nota})


# ------------------------------------------------------------------ formatos exclusivos da Soares (16/11/2026)
# foto (foto do Jailson/escritório da pasta 01 ENTRADA), jurisprudencia (tese em 1 lâmina), glossario
# (termo explicado) e serie ("As 3 formas de cobrar na Justiça", quadro fixo da série).
def l_foto(l, n, total, tema=""):
    """Post de foto: foto real (01 ENTRADA) em tela cheia, frase curta e marca discreta.
    {"layout": "foto", "imagem": "caminho/arquivo.jpg", "frase": "...", "legenda": "...", "posicao": "center"}"""
    img = l.get("imagem")
    if img and os.path.exists(img):
        src = "file://" + os.path.abspath(img)
        fundo = (f'<img src="{src}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;'
                 f'object-position:{l.get("posicao", "center")}">')
    else:
        fundo = (f'<div style="position:absolute;inset:0;background:repeating-linear-gradient(135deg,#C9BFA9 0 40px,#D8CFBC 40px 80px)"></div>'
                 f'<div style="position:absolute;left:150px;right:150px;top:330px;height:300px;border:4px dashed {DARK};border-radius:24px;'
                 f'display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px">'
                 f'<p style="margin:0;font-size:40px;font-weight:700;color:{DARK}">FOTO DO JAILSON / ESCRITÓRIO</p>'
                 f'<p style="margin:0;font-size:28px;color:{DARK}">vem da pasta 01 ENTRADA</p></div>')
    veu = '<div style="position:absolute;left:0;right:0;bottom:0;height:62%;background:linear-gradient(180deg,rgba(31,58,61,0) 0%,rgba(31,58,61,.88) 45%,rgba(31,58,61,.97) 100%)"></div>'
    corpo = (fundo + veu +
             f'<div style="position:absolute;left:64px;top:64px;padding:22px 30px;background:rgba(31,58,61,.88);border-radius:18px">{horiz(0.55)}</div>'
             f'<div style="position:absolute;left:88px;right:88px;bottom:88px;display:flex;flex-direction:column;gap:30px">'
             f'<div style="width:110px;height:6px;background:{GOLD}"></div>'
             f'<p style="margin:0;font-size:{l.get("tamanho", 64)}px;font-weight:700;line-height:1.12;letter-spacing:-1.2px;color:{LIGHT}">{e(l.get("frase"))}</p>'
             f'<div style="display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid rgba(244,241,234,.35);padding-top:22px">'
             f'<p style="margin:0;font-size:24px;font-weight:500;color:{LIGHT};opacity:.85">{e(l.get("legenda", "Jailson Soares · OAB/RS 115.168"))}</p>'
             f'{assinatura(LIGHT, GOLD, 16)}</div></div>')
    return abs_caixa(DARK, corpo)


def l_jurisprudencia(l, n, total, tema=""):
    """Jurisprudência em uma lâmina: tese (alto, verde) + "o que muda para a sua empresa" (baixo, creme).
    {"layout": "jurisprudencia", "tribunal": "STJ", "tese": "...", "referencia": "Súmula 299/STJ", "pratica": "..."}"""
    alto = (f'<div style="position:absolute;left:0;right:0;top:0;height:770px;background:{DARK};overflow:hidden">'
            f'<div style="position:absolute;right:-160px;top:200px;opacity:.06">{mark(700, LIGHT, LIGHT)}</div>'
            f'<div style="position:absolute;left:88px;right:88px;top:88px;display:flex;justify-content:space-between;align-items:center">'
            f'{horiz(0.55)}<p style="margin:0;padding:10px 24px;border:2px solid {GOLD};border-radius:999px;font-size:21px;font-weight:700;'
            f'letter-spacing:3px;color:{GOLD}">JURISPRUDÊNCIA · {e(l.get("tribunal", "STJ"))}</p></div>'
            f'<div style="position:absolute;left:88px;right:88px;top:230px;bottom:90px;display:flex;align-items:center;gap:34px">'
            f'<div style="flex:none;align-self:stretch;width:8px;background:{GOLD}"></div>'
            f'<div><p style="margin:0;font-size:{l.get("tamanho", 66)}px;font-weight:700;line-height:1.14;letter-spacing:-1.2px;color:{LIGHT}">{e(l.get("tese"))}</p>'
            f'<p style="margin:26px 0 0;font-size:25px;font-weight:600;letter-spacing:1px;color:{GOLD}">{e(l.get("referencia"))}</p></div></div></div>')
    baixo = (f'<div style="position:absolute;left:88px;right:88px;top:830px;bottom:88px;display:flex;flex-direction:column;justify-content:space-between">'
             f'<div><p style="margin:0 0 18px;font-size:25px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:{GOLDD}">O que muda para a sua empresa</p>'
             f'<p style="margin:0;font-size:33px;line-height:1.45;color:{INK}">{e(l.get("pratica"))}</p></div>{base_feed(False)}</div>')
    return abs_caixa(CREAM, alto + baixo)


def l_glossario(l, n, total, tema=""):
    """Glossário do empresário: um termo jurídico explicado em linguagem simples.
    {"layout": "glossario", "numero": "01", "termo": "...", "classe": "...", "definicao": "...", "pratica": "...", "base": "CPC, art. 784"}"""
    meio = (f'<div>'
            f'<p style="margin:0 0 30px;font-size:24px;font-weight:700;letter-spacing:5px;color:{GOLDD}">GLOSSÁRIO DO EMPRESÁRIO · Nº {e(l.get("numero", "01"))}</p>'
            f'<p style="margin:0;font-size:{l.get("tamanho", 74)}px;font-weight:700;line-height:1.04;letter-spacing:-2px;color:{DARK}">{e(l.get("termo"))}</p>'
            f'<p style="margin:16px 0 0;font-size:28px;font-style:italic;color:{MUTED}">{e(l.get("classe", "direito empresarial"))}</p>'
            f'<div style="width:110px;height:6px;background:{GOLD};margin:34px 0"></div>'
            f'<p style="margin:0;font-size:35px;line-height:1.45;color:{INK}">{e(l.get("definicao"))}</p>'
            f'<div style="margin-top:38px;background:#fff;border-radius:22px;padding:30px 36px;border-left:0">'
            f'<p style="margin:0 0 10px;font-size:23px;font-weight:700;letter-spacing:4px;color:{GOLDD}">NA PRÁTICA</p>'
            f'<p style="margin:0;font-size:30px;line-height:1.42;color:{INK}">{e(l.get("pratica"))}</p></div>'
            f'<p style="margin:22px 0 0;font-size:22px;font-weight:500;color:{MUTED}">{e(l.get("base", ""))}</p></div>')
    return moldura(SAND, False, n, total, meio, marca_fundo(False, right=-120, top=-60, px=380))


def l_serie(l, n, total, tema=""):
    """Quadro fixo da série "As 3 formas de cobrar na Justiça" (sempre o mesmo desenho; "destaque" = 0, 1 ou 2).
    {"layout": "serie", "numero": "1", "titulo": "...", "colunas": ["Ação de cobrança", "Ação monitória", "Execução"],
     "linhas": [{"rotulo": "Documento", "itens": ["...", "...", "..."]}], "destaque": 2, "nota": "..."}"""
    cols = l.get("colunas", ["Ação de cobrança", "Ação monitória", "Execução de título"])
    dst = l.get("destaque", -1)
    cab = f'<div style="width:170px"></div>' + "".join(
        f'<div style="flex:1;background:{GOLD if i == dst else DARK};border-radius:16px 16px 0 0;padding:20px 14px;text-align:center;'
        f'font-size:25px;font-weight:700;line-height:1.15;color:{DARK if i == dst else LIGHT}">{e(c)}</div>' for i, c in enumerate(cols))
    linhas = ""
    for r in l.get("linhas", []):
        cel = "".join(
            f'<div style="flex:1;background:{"#FBF3E4" if i == dst else "#fff"};padding:20px 16px;font-size:23px;line-height:1.35;color:{INK}">{e(t)}</div>'
            for i, t in enumerate(r.get("itens", [])))
        linhas += (f'<div style="display:flex;gap:10px;margin-top:10px"><div style="width:170px;padding:20px 0;font-size:22px;font-weight:700;'
                   f'letter-spacing:1px;text-transform:uppercase;color:{GOLDD}">{e(r.get("rotulo"))}</div>{cel}</div>')
    meio = (f'<div>'
            f'<p style="margin:0 0 12px;font-size:24px;font-weight:700;letter-spacing:5px;color:{GOLDD}">SÉRIE · AS 3 FORMAS DE COBRAR NA JUSTIÇA · Nº {e(l.get("numero", "1"))}</p>'
            f'<p style="margin:0 0 40px;font-size:{l.get("tamanho", 50)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<div style="display:flex;gap:10px">{cab}</div>{linhas}'
            f'<p style="margin:26px 0 0;font-size:22px;color:{MUTED}">{e(l.get("nota", ""))}</p></div>')
    return moldura(CREAM, False, n, total, meio)


LAYOUTS.update({"foto": l_foto, "jurisprudencia": l_jurisprudencia, "glossario": l_glossario, "serie": l_serie})


# ------------------------------------------------------------------ estruturas visuais extras (16/11/2026)
# split, palavra, linha_tempo, grade, marcatexto, fluxo, moldura, ranking – servem para qualquer assunto.
def _img_ou_vazio(img, estilo, rotulo="FOTO"):
    if img and os.path.exists(img):
        return f'<img src="file://{os.path.abspath(img)}" style="{estilo};object-fit:cover">'
    return (f'<div style="{estilo};background:repeating-linear-gradient(135deg,#C9BFA9 0 34px,#D8CFBC 34px 68px);'
            f'display:flex;align-items:center;justify-content:center"><p style="margin:0;padding:14px 26px;background:rgba(247,245,240,.85);'
            f'border-radius:12px;font-size:28px;font-weight:700;letter-spacing:3px;color:{DARK}">{rotulo}</p></div>')


def l_split(l, n, total, tema=""):
    """Tela dividida: metade verde (ou foto) com título, metade clara com texto.
    {"layout": "split", "chamada": "...", "titulo": "...", "texto": "...", "imagem": "opcional"}"""
    if l.get("imagem"):
        esq = _img_ou_vazio(l.get("imagem"), "position:absolute;left:0;top:0;width:540px;height:1350px")
        tit = (f'<p style="position:absolute;left:600px;right:88px;top:330px;margin:0;font-size:{l.get("tamanho", 58)}px;font-weight:700;'
               f'line-height:1.1;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>')
        corpo = esq + tit
        txt_top = 640
    else:
        corpo = (f'<div style="position:absolute;left:0;top:0;width:540px;height:1350px;background:{DARK};overflow:hidden">'
                 f'<div style="position:absolute;left:-160px;bottom:-60px;opacity:.07">{mark(700, LIGHT, LIGHT)}</div>'
                 f'<div style="position:absolute;left:70px;top:70px">{horiz(0.5)}</div>'
                 f'<p style="position:absolute;left:70px;right:56px;top:340px;margin:0;font-size:24px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:{GOLD}">{e(l.get("chamada", ""))}</p>'
                 f'<p style="position:absolute;left:70px;right:56px;top:400px;margin:0;font-size:{l.get("tamanho", 62)}px;font-weight:700;line-height:1.08;letter-spacing:-1.5px;color:{LIGHT}">{e(l.get("titulo"))}</p></div>')
        txt_top = 400
    corpo += (f'<div style="position:absolute;left:600px;right:80px;top:{txt_top}px"><div style="width:90px;height:6px;background:{GOLD};margin-bottom:34px"></div>'
              f'<p style="margin:0;font-size:34px;line-height:1.48;color:{INK}">{e(l.get("texto"))}</p></div>'
              f'<div style="position:absolute;left:600px;right:80px;bottom:80px;border-top:2px solid {LINHA};padding-top:20px;display:flex;justify-content:flex-end">{assinatura(DARK, GOLDD, 15)}</div>')
    return abs_caixa(CREAM, corpo)


def l_palavra(l, n, total, tema=""):
    """Palavra gigante: uma palavra ocupa a lâmina; frase curta embaixo.
    {"layout": "palavra", "palavra": "Prazo.", "frase": "...", "fundo": "escuro|claro"}"""
    bg, txt, dest, esc = cores(l, "escuro")
    meio = (f'<div><p data-fit="904" style="margin:0;white-space:nowrap;font-size:{l.get("tamanho", 300)}px;font-weight:700;line-height:.95;'
            f'letter-spacing:-10px;color:{GOLD if esc else DARK}">{e(l.get("palavra"))}</p>'
            f'<div style="width:120px;height:6px;background:{GOLD};margin:46px 0 36px"></div>'
            f'<p style="margin:0;max-width:860px;font-size:44px;font-weight:500;line-height:1.3;color:{txt}">{e(l.get("frase"))}</p></div>')
    return moldura(bg, esc, n, total, meio)


def l_linha_tempo(l, n, total, tema=""):
    """Linha do tempo vertical com marcos.
    {"layout": "linha_tempo", "chamada": "...", "titulo": "...", "marcos": [{"quando": "...", "titulo": "...", "texto": "..."}]}"""
    ms = l.get("marcos", [])
    itens = ""
    for i, m in enumerate(ms):
        ult = i == len(ms) - 1
        trilho = "" if ult else f'<div style="width:4px;flex:1;background:{LINHA}"></div>'
        itens += (f'<div style="display:flex;gap:30px;position:relative">'
                  f'<div style="flex:none;width:170px;text-align:right;padding-top:6px;font-size:28px;font-weight:700;color:{GOLDD}">{e(m.get("quando"))}</div>'
                  f'<div style="flex:none;display:flex;flex-direction:column;align-items:center">'
                  f'<div style="width:34px;height:34px;border-radius:50%;margin-top:6px;background:{GOLD if ult else DARK};border:5px solid {CREAM};box-shadow:0 0 0 3px {GOLD if ult else DARK}"></div>'
                  f'{trilho}</div>'
                  f'<div style="padding-bottom:40px"><p style="margin:0;font-size:36px;font-weight:700;color:{DARK}">{e(m.get("titulo"))}</p>'
                  f'<p style="margin:8px 0 0;font-size:28px;line-height:1.4;color:{INK}">{e(m.get("texto"))}</p></div></div>')
    meio = (f'<div><p style="margin:0 0 12px;font-size:24px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:{GOLDD}">{e(l.get("chamada", ""))}</p>'
            f'<p style="margin:0 0 50px;font-size:{l.get("tamanho", 56)}px;font-weight:700;line-height:1.1;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>{itens}</div>')
    return moldura(CREAM, False, n, total, meio)


def l_grade(l, n, total, tema=""):
    """Grade 2x2: quatro blocos com número/sigla e título curto.
    {"layout": "grade", "titulo": "...", "blocos": [{"topo": "01", "titulo": "...", "texto": "..."}] x4}"""
    bl = l.get("blocos", [])[:4]
    cards = ""
    for i, b in enumerate(bl):
        esc = i in (0, 3)
        cards += (f'<div style="background:{DARK if esc else "#fff"};border-radius:24px;padding:36px 34px;display:flex;flex-direction:column;gap:14px">'
                  f'<p style="margin:0;font-size:56px;font-weight:700;line-height:1;color:{GOLD if esc else GOLDD}">{e(b.get("topo", f"{i+1:02d}"))}</p>'
                  f'<p style="margin:0;font-size:34px;font-weight:700;line-height:1.15;color:{LIGHT if esc else DARK}">{e(b.get("titulo"))}</p>'
                  f'<p style="margin:0;font-size:26px;line-height:1.4;color:{"#D9D2C3" if esc else INK}">{e(b.get("texto"))}</p></div>')
    meio = (f'<div><p style="margin:0 0 40px;font-size:{l.get("tamanho", 54)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;grid-auto-rows:330px;gap:22px">{cards}</div></div>')
    return moldura(SAND, False, n, total, meio)


def l_marcatexto(l, n, total, tema=""):
    """Documento com marca-texto: folha de papel, trecho grifado em dourado e anotação na margem.
    {"layout": "marcatexto", "chamada": "...", "cabecalho": "Art. 784 – CPC", "antes": "...", "grifo": "...", "depois": "...", "nota": "..."}"""
    folha = (f'<div style="position:relative;background:#fff;border-radius:6px;box-shadow:0 20px 50px rgba(31,58,61,.16);'
             f'padding:60px 60px 66px;transform:rotate(-1.2deg)">'
             f'<p style="margin:0 0 26px;font-size:24px;font-weight:700;letter-spacing:3px;color:{MUTED}">{e(l.get("cabecalho", ""))}</p>'
             f'<p style="margin:0;font-family:Georgia,serif;font-size:40px;line-height:1.6;color:{INK}">{e(l.get("antes"))} '
             f'<span style="background:linear-gradient(180deg,transparent 45%,rgba(194,154,91,.55) 45%);font-weight:700;color:{DARK}">{e(l.get("grifo"))}</span> '
             f'{e(l.get("depois"))}</p></div>')
    nota = (f'<div style="display:flex;justify-content:flex-end;align-items:flex-start;gap:14px;margin-top:34px;padding-right:20px">'
            f'<svg width="80" height="70" viewBox="0 0 80 70"><path d="M70 64 C60 30 40 14 10 8 M10 8 L26 2 M10 8 L22 20" fill="none" stroke="{GOLDD}" stroke-width="4" stroke-linecap="round"></path></svg>'
            f'<p style="margin:20px 0 0;max-width:560px;font-size:32px;font-weight:600;line-height:1.3;color:{GOLDD}">{e(l.get("nota"))}</p></div>')
    meio = (f'<div style="position:relative"><p style="margin:0 0 40px;font-size:24px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:{GOLDD}">{e(l.get("chamada", ""))}</p>'
            f'{folha}{nota}</div>')
    return moldura(SAND, False, n, total, meio)


def l_fluxo(l, n, total, tema=""):
    """Fluxograma: pergunta inicial, duas respostas (sim/não) e um resultado para cada.
    {"layout": "fluxo", "titulo": "...", "pergunta": "...", "sim": "...", "nao": "...", "rot_sim": "Sim", "rot_nao": "Não"}"""
    def box(t, bg, c, w="100%"):
        return f'<div style="width:{w};box-sizing:border-box;background:{bg};border-radius:20px;padding:30px 30px;font-size:32px;font-weight:700;line-height:1.25;color:{c};text-align:center">{e(t)}</div>'
    seta = (f'<svg width="904" height="150" viewBox="0 0 904 150"><path d="M452 0 V40 M452 40 H226 V140 M452 40 H678 V140" fill="none" stroke="{GOLDD}" stroke-width="4"></path>'
            f'<path d="M214 124 L226 144 L238 124 M666 124 L678 144 L690 124" fill="none" stroke="{GOLDD}" stroke-width="4"></path>'
            f'<rect x="150" y="62" width="150" height="44" rx="22" fill="{CREAM}" stroke="{GOLDD}" stroke-width="2"></rect>'
            f'<text x="225" y="92" text-anchor="middle" font-family="Montserrat" font-weight="700" font-size="24" fill="{GOLDD}">{e(l.get("rot_sim", "Sim"))}</text>'
            f'<rect x="603" y="62" width="150" height="44" rx="22" fill="{CREAM}" stroke="{GOLDD}" stroke-width="2"></rect>'
            f'<text x="678" y="92" text-anchor="middle" font-family="Montserrat" font-weight="700" font-size="24" fill="{GOLDD}">{e(l.get("rot_nao", "Não"))}</text></svg>')
    meio = (f'<div><p style="margin:0 0 44px;font-size:{l.get("tamanho", 54)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>'
            f'{box(l.get("pergunta"), DARK, LIGHT)}{seta}'
            f'<div style="display:flex;gap:28px">{box(l.get("sim"), GOLD, DARK, "50%")}{box(l.get("nao"), "#fff", DARK, "50%")}</div></div>')
    return moldura(CREAM, False, n, total, meio)


def l_moldura(l, n, total, tema=""):
    """Foto em moldura clara, levemente inclinada, com texto ao lado/embaixo.
    {"layout": "moldura", "imagem": "...", "legenda": "...", "titulo": "...", "texto": "..."}"""
    foto = (f'<div style="position:absolute;left:110px;top:200px;width:560px;background:#fff;padding:22px 22px 70px;'
            f'box-shadow:0 22px 50px rgba(0,0,0,.28);transform:rotate(-3deg)">'
            f'{_img_ou_vazio(l.get("imagem"), "display:block;width:516px;height:600px")}'
            f'<p style="margin:18px 0 0;font-family:Georgia,serif;font-style:italic;font-size:24px;color:{MUTED};text-align:center">{e(l.get("legenda", ""))}</p></div>')
    txt = (f'<div style="position:absolute;left:88px;right:88px;top:1000px"><p style="margin:0;font-size:{l.get("tamanho", 50)}px;font-weight:700;line-height:1.12;letter-spacing:-1px;color:{LIGHT}">{e(l.get("titulo"))}</p>'
           f'<p style="margin:16px 0 0;font-size:30px;line-height:1.4;color:#D9D2C3">{e(l.get("texto"))}</p></div>')
    corpo = (f'<div style="position:absolute;right:-200px;top:120px;opacity:.07">{mark(760, LIGHT, LIGHT)}</div>'
             f'<div style="position:absolute;right:88px;top:88px">{horiz(0.5)}</div>{foto}{txt}')
    return abs_caixa(DARK, corpo)


def l_ranking(l, n, total, tema=""):
    """Ranking numerado: números grandes em coluna, título e texto ao lado.
    {"layout": "ranking", "chamada": "...", "titulo": "...", "itens": [{"titulo": "...", "texto": "..."}]}"""
    its = ""
    for i, it in enumerate(l.get("itens", [])[:4], 1):
        its += (f'<div style="display:flex;gap:34px;align-items:center;padding:26px 0;border-top:2px solid {LINHA}">'
                f'<p style="margin:0;flex:none;width:150px;font-size:150px;font-weight:700;line-height:.85;letter-spacing:-6px;color:{GOLD if i == 1 else DARK}">{i}</p>'
                f'<div><p style="margin:0;font-size:38px;font-weight:700;line-height:1.15;color:{DARK}">{e(it.get("titulo"))}</p>'
                f'<p style="margin:8px 0 0;font-size:28px;line-height:1.4;color:{INK}">{e(it.get("texto"))}</p></div></div>')
    meio = (f'<div><p style="margin:0 0 12px;font-size:24px;font-weight:700;letter-spacing:5px;text-transform:uppercase;color:{GOLDD}">{e(l.get("chamada", ""))}</p>'
            f'<p style="margin:0 0 36px;font-size:{l.get("tamanho", 56)}px;font-weight:700;line-height:1.1;letter-spacing:-1px;color:{DARK}">{e(l.get("titulo"))}</p>{its}</div>')
    return moldura(CREAM, False, n, total, meio)


def l_foto_fundo(l, n, total, tema=""):
    """Foto de fundo (qualquer foto do Jailson) com a identificação do escritório nos quatro cantos:
    logo (alto-esq.), @soaresadvc (alto-dir.), site/OAB (baixo-esq.), assinatura (baixo-dir.) e filete dourado.
    Texto é opcional ("legenda", curta). Faixas escuras só no alto e no pé, para a foto continuar aparecendo.
    {"layout": "foto_fundo", "imagem": "arquivo.jpg", "legenda": "opcional", "posicao": "center", "filete": true}"""
    img = l.get("imagem")
    if img and os.path.exists(img):
        fundo = (f'<img src="file://{os.path.abspath(img)}" style="position:absolute;inset:0;width:100%;height:100%;'
                 f'object-fit:cover;object-position:{l.get("posicao", "center")}">')
    else:
        fundo = _img_ou_vazio(None, "position:absolute;inset:0;width:100%;height:100%", "FOTO DO JAILSON")
    faixas = ('<div style="position:absolute;left:0;right:0;top:0;height:300px;background:linear-gradient(180deg,rgba(20,38,40,.78),rgba(20,38,40,0))"></div>'
              '<div style="position:absolute;left:0;right:0;bottom:0;height:360px;background:linear-gradient(0deg,rgba(20,38,40,.85),rgba(20,38,40,0))"></div>')
    filete = (f'<div style="position:absolute;inset:36px;border:2px solid rgba(194,154,91,.85);border-radius:4px"></div>'
              if l.get("filete", True) else "")
    leg = (f'<p style="position:absolute;left:88px;right:88px;bottom:190px;margin:0;font-size:{l.get("tamanho", 40)}px;font-weight:700;'
           f'line-height:1.2;color:{LIGHT};text-shadow:0 2px 12px rgba(0,0,0,.45)">{e(l.get("legenda"))}</p>' if l.get("legenda") else "")
    cantos = (f'<div style="position:absolute;left:84px;top:84px">{horiz(0.55)}</div>'
              f'<div style="position:absolute;right:84px;top:104px;display:flex;align-items:center;gap:12px">'
              f'<p style="margin:0;font-size:26px;font-weight:600;color:{LIGHT}">@soaresadvc</p></div>'
              f'<div style="position:absolute;left:84px;right:84px;bottom:84px;display:flex;justify-content:space-between;align-items:flex-end">'
              f'<p style="margin:0;font-size:22px;font-weight:500;color:{LIGHT};opacity:.9">advocaciasoares.com · OAB/RS 115.168</p>'
              f'{assinatura(LIGHT, GOLD, 16)}</div>')
    return abs_caixa(DARK, fundo + faixas + filete + leg + cantos)


LAYOUTS.update({"foto_fundo": l_foto_fundo})
LAYOUTS.update({"split": l_split, "palavra": l_palavra, "linha_tempo": l_linha_tempo, "grade": l_grade,
                "marcatexto": l_marcatexto, "fluxo": l_fluxo, "moldura": l_moldura, "ranking": l_ranking})


# ------------------------------------------------------------------ peças largas (cortadas em várias imagens)
# 1) MOSAICO: 3 posts que formam uma imagem só na grade do perfil.
#    Desde 2025 a grade recorta cada post em 3:4 (só os 1012 px centrais de cada imagem 1080x1350). A arte larga
#    tem 3 x 1012 px visíveis + 34 px de sobra em cada ponta, e cada imagem leva 34 px extras de cada lado.
#    Gera 01 (esquerda), 02 (meio), 03 (direita); na planilha publicar 03, depois 02 e por último 01.
# 2) JORNADA: carrossel panorâmico contínuo (uma linha atravessa as lâminas ao deslizar).
GRADE_VIS, GRADE_SOBRA = 1012, 34


def w_mosaico(p):
    bg, txt, dest, esc = cores(p, "escuro")
    W = 3 * GRADE_VIS + 2 * GRADE_SOBRA
    x0 = GRADE_SOBRA
    rod = p.get("rodapes", ["", "", ""])
    rodapes = "".join(
        f'<div style="position:absolute;left:{x0 + i * GRADE_VIS + 70}px;width:{GRADE_VIS - 140}px;bottom:100px;font-size:30px;line-height:1.38;color:{txt}">{e(t)}</div>'
        for i, t in enumerate(rod))
    c, g = (LIGHT, GOLD) if esc else (DARK, GOLDD)
    corpo = (
        f'<div style="position:absolute;right:-40px;top:-60px;opacity:{0.07 if esc else 0.05}">{mark(1500, c, c)}</div>'
        f'<div style="position:absolute;left:0;right:0;top:930px;height:8px;background:{GOLD}"></div>'
        f'<div style="position:absolute;left:{x0 + 70}px;top:100px">{horiz(0.75, c, g)}</div>'
        f'<p style="position:absolute;left:{x0 + 70}px;top:300px;margin:0;font-size:32px;font-weight:700;letter-spacing:8px;text-transform:uppercase;color:{g}">{e(p.get("chamada", ""))}</p>'
        f'<p data-fit="{3 * GRADE_VIS - 150}" style="position:absolute;left:{x0 + 60}px;top:370px;margin:0;white-space:nowrap;font-size:{p.get("tamanho", 330)}px;'
        f'font-weight:700;letter-spacing:-8px;line-height:1;color:{GOLD if esc else DARK}">{e(p.get("titulo"))}</p>'
        f'<p style="position:absolute;left:{x0 + 70}px;top:985px;width:{2 * GRADE_VIS}px;margin:0;font-size:50px;line-height:1.25;color:{txt}">{e(p.get("texto"))}</p>'
        f'{rodapes}'
        f'<div style="position:absolute;left:{x0 + 2 * GRADE_VIS + 70}px;width:{GRADE_VIS - 140}px;bottom:220px;display:flex;justify-content:flex-end">{assinatura(c, g, 18)}</div>')
    return W, f'<div id="r" style="width:{W}px;height:1350px;background:{bg};position:relative;overflow:hidden;{F}">{corpo}</div>', \
        [(i * GRADE_VIS, 1080) for i in range(3)]


def w_jornada(p):
    """Carrossel panorâmico: uma linha contínua atravessa as lâminas, com uma etapa em cada."""
    passos = p.get("passos", [])
    n = len(passos) + 1
    W = n * 1080
    Y = 760
    marcos = ""
    for i, s in enumerate(passos, 1):
        cx = i * 1080 + 540
        ult = i == len(passos)
        marcos += (
            f'<p style="position:absolute;left:{i * 1080 + 640}px;top:20px;margin:0;font-size:420px;font-weight:700;line-height:1;color:{SAND}">{i}</p>'
            f'<div style="position:absolute;left:{cx - 70}px;top:{Y - 70}px;width:140px;height:140px;border-radius:50%;box-sizing:border-box;'
            f'background:{GOLD if ult else CREAM};border:6px solid {GOLD if ult else DARK};display:flex;align-items:center;justify-content:center;'
            f'font-size:62px;font-weight:700;color:{DARK}">{i}</div>'
            f'<p style="position:absolute;left:{i * 1080 + 110}px;width:860px;top:300px;margin:0;font-size:26px;font-weight:700;letter-spacing:6px;color:{GOLDD}">ETAPA {i} DE {len(passos)}</p>'
            f'<p style="position:absolute;left:{i * 1080 + 110}px;width:860px;top:350px;margin:0;font-size:{s.get("tamanho", 72)}px;font-weight:700;line-height:1.1;letter-spacing:-1.5px;color:{DARK}">{e(s.get("titulo"))}</p>'
            f'<p style="position:absolute;left:{i * 1080 + 110}px;width:820px;top:{Y + 130}px;margin:0;font-size:40px;line-height:1.42;color:{INK}">{e(s.get("texto"))}</p>'
            f'<div style="position:absolute;left:{i * 1080 + 88}px;width:904px;bottom:88px;display:flex;justify-content:space-between;align-items:flex-end;border-top:2px solid {LINHA};padding-top:22px">'
            f'{contador(i + 1, n, INK, GOLDD)}{assinatura(DARK, GOLDD, 16)}</div>')
    corpo = (
        f'<div style="position:absolute;left:0;top:0;width:1080px;height:1350px;background:{DARK};overflow:hidden">'
        f'<div style="position:absolute;right:-180px;top:280px;opacity:.07">{mark(1100, LIGHT, LIGHT)}</div></div>'
        f'<div style="position:absolute;left:88px;top:88px">{selo()}</div>'
        f'<p style="position:absolute;left:88px;top:300px;margin:0;font-size:24px;font-weight:600;letter-spacing:5px;text-transform:uppercase;color:{GOLD}">{e(p.get("tema", ""))}</p>'
        f'<p style="position:absolute;left:88px;width:880px;top:350px;margin:0;font-size:{p.get("tamanho", 78)}px;font-weight:700;line-height:1.06;letter-spacing:-2px;color:{LIGHT}">{e(p.get("titulo"))}</p>'
        f'<p style="position:absolute;left:88px;width:450px;top:{Y + 90}px;margin:0;font-size:36px;line-height:1.35;color:#D9D2C3">{e(p.get("subtitulo", ""))}</p>'
        f'<div style="position:absolute;left:88px;bottom:88px">{contador(1, n, LIGHT, GOLD)}</div>'
        f'<div style="position:absolute;right:{W - 1080 + 88}px;bottom:88px">{seta(LIGHT, GOLD)}</div>'
        f'<div style="position:absolute;left:640px;right:540px;top:{Y - 5}px;height:10px;background:{GOLD}"></div>'
        f'<div style="position:absolute;left:560px;top:{Y - 40}px;width:80px;height:80px;border-radius:50%;background:{GOLD}"></div>'
        f'{marcos}')
    return W, f'<div id="r" style="width:{W}px;height:1350px;background:{CREAM};position:relative;overflow:hidden;{F}">{corpo}</div>', \
        [(i * 1080, 1080) for i in range(n)]


LARGOS = {"mosaico": w_mosaico, "jornada": w_jornada}


def renderizar_largo(post, saida, chrome=None):
    """Renderiza a peça larga uma vez e corta nas imagens. No mosaico, 01 = esquerda, 02 = meio, 03 = direita
    (na planilha, publicar 03 primeiro, depois 02 e por último 01)."""
    os.makedirs(saida, exist_ok=True)
    p = post["largo"]
    W, corpo, cortes = LARGOS[p["layout"]](p)
    arquivos = []
    with sync_playwright() as pw:
        kw = {"executable_path": chrome} if chrome else {}
        b = pw.chromium.launch(args=["--allow-file-access-from-files"], **kw)
        pg = b.new_page(viewport={"width": W, "height": 1350})
        tmp = os.path.join(saida, "_tmp.html")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>{fontcss()} html,body{{margin:0}} body{{{F}}}</style></head><body>{corpo}</body></html>')
        pg.goto("file://" + os.path.abspath(tmp))
        pg.evaluate("document.fonts.ready.then(()=>1)")
        pg.evaluate("""() => document.querySelectorAll('[data-fit]').forEach(el => {
            const alvo = +el.dataset.fit, fs = parseFloat(getComputedStyle(el).fontSize);
            el.style.fontSize = Math.min(fs * alvo / el.scrollWidth, 480) + 'px'; })""")
        pg.wait_for_timeout(300)
        pg.locator("#r").screenshot(path=os.path.join(saida, "_inteira.png"))
        for i, (x, w) in enumerate(cortes, 1):
            a = os.path.join(saida, f"{i:02d}.png")
            pg.screenshot(path=a, clip={"x": x, "y": 0, "width": w, "height": 1350})
            arquivos.append(a)
        os.remove(tmp)
        b.close()
    return arquivos


def fontcss():
    return "".join(f"@font-face{{font-family:Montserrat;font-weight:{w};src:url('file://{AQUI}/fonts/montserrat-latin-{w}-normal.woff2') format('woff2');}}"
                   for w in (300, 400, 500, 600, 700))


def renderizar(post, saida, chrome=None):
    os.makedirs(saida, exist_ok=True)
    laminas = post["laminas"]
    total = len(laminas)
    arquivos = []
    with sync_playwright() as pw:
        kw = {"executable_path": chrome} if chrome else {}
        b = pw.chromium.launch(args=["--allow-file-access-from-files"], **kw)
        pg = b.new_page()
        tmp = os.path.join(saida, "_tmp.html")
        for i, l in enumerate(laminas, 1):
            corpo = LAYOUTS[l.get("layout", "topico")](l, i, total, post.get("tema", "Recuperação de ativos"))
            with open(tmp, "w", encoding="utf-8") as f:
                f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>{fontcss()} html,body{{margin:0}} body{{{F}}}</style></head>'
                        f'<body><div id="r" style="display:inline-block">{corpo}</div></body></html>')
            pg.goto("file://" + os.path.abspath(tmp))
            pg.evaluate("document.fonts.ready.then(()=>1)")
            pg.evaluate("""() => document.querySelectorAll('[data-fit]').forEach(el => {
                const alvo = +el.dataset.fit, fs = parseFloat(getComputedStyle(el).fontSize);
                if (el.scrollWidth > alvo) el.style.fontSize = (fs * alvo / el.scrollWidth) + 'px'; })""")
            pg.wait_for_timeout(100)
            p = os.path.join(saida, f"{i:02d}.png")
            pg.locator("#r").screenshot(path=p)
            arquivos.append(p)
        os.remove(tmp)
        b.close()
    return arquivos


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as f:
        post = json.load(f)
    chrome = os.environ.get("CHROME_PATH")
    fn = renderizar_largo if "largo" in post else renderizar
    for a in fn(post, sys.argv[2], chrome):
        print(a)
