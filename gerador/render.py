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
    {"layout": "story_numero", "numero": "9,3 mi", "titulo": "...", "fonte": "Serasa Experian, ago/2026"}
  ]
}
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
    for a in renderizar(post, sys.argv[2], chrome):
        print(a)
