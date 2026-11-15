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
