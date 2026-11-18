"""
Relatório semanal de resultados (Instagram + Facebook) – GRUPO JASA.

Roda no GitHub Actions (relatorio.yml) com os mesmos Secrets/Variables do publicador:
  META_TOKEN, IG_USER_ID, FB_PAGE_ID   (MARCA = "Advocacia Soares" ou "Justo Acordo")
Gera relatorios/AAAA-MM-DD.md e relatorios/ultimo.md (lidos pela tarefa de domingo, que põe o resumo no e-mail único).

Mostra: seguidores (IG/FB), alcance e interações da conta nos últimos 7 dias, e os posts de feed dos últimos
30 dias com alcance, curtidas, comentários, salvamentos e compartilhamentos, mais os CANDIDATOS A TURBINAR
(melhor engajamento por alcance). Stories só ficam disponíveis por 24 h na API e não entram.
Se faltar permissão no token (ex.: instagram_manage_insights / read_insights), o relatório diz o que faltou.
"""
import csv, datetime as dt, json, os, urllib.parse, urllib.request

GRAPH = "https://graph.facebook.com/v21.0"
TOKEN = os.environ.get("META_TOKEN", "").strip()
IG = os.environ.get("IG_USER_ID", "").strip()
FB = os.environ.get("FB_PAGE_ID", "").strip()
MARCA = os.environ.get("MARCA", "").strip() or "Marca"
avisos = []


def api(path, **params):
    params["access_token"] = TOKEN
    url = f"{GRAPH}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("error", {}).get("message", str(e))
        except Exception:
            msg = str(e)
        avisos.append(f"{path.split('?')[0]} → {msg[:160]}")
        return {}


def ids_dos_posts():
    m = {}
    if os.path.exists("status.csv"):
        for row in csv.reader(open("status.csv", encoding="utf-8")):
            if len(row) > 3 and "IG " in row[3]:
                ig = row[3].split("IG ")[1].split()[0].strip("|")
                m[ig] = row[0]
    return m


def n(x):
    return f"{int(x):,}".replace(",", ".") if isinstance(x, (int, float)) else "–"


def descobrir_ids():
    """Sem IG_USER_ID/FB_PAGE_ID configurados, descobre pelo token (Página cujo nome contém a marca)."""
    global IG, FB
    if IG and FB:
        return
    pags = api("me/accounts", fields="id,name,instagram_business_account").get("data", [])
    chave = "soares" if "soares" in MARCA.lower() else "justo"
    pag = next((p for p in pags if chave in p.get("name", "").lower()), {})
    FB = FB or pag.get("id", "")
    IG = IG or pag.get("instagram_business_account", {}).get("id", "")


def main():
    hoje = dt.date.today()
    if TOKEN:
        descobrir_ids()
    linhas = [f"# Resultados – {MARCA} – semana até {hoje:%d/%m/%Y}", ""]
    if not TOKEN:
        linhas.append("Sem META_TOKEN: relatório não gerado.")
        return salvar(hoje, linhas)

    conta = api(IG, fields="username,followers_count,media_count")
    pagina = api(FB, fields="name,followers_count,fan_count") if FB else {}
    anterior = ler_anterior()
    seg = conta.get("followers_count")
    var = f" ({seg - anterior:+d} na semana)" if isinstance(seg, int) and isinstance(anterior, int) else ""
    linhas += [f"**Instagram @{conta.get('username', '?')}:** {n(seg)} seguidores{var} · {n(conta.get('media_count'))} publicações",
               f"**Facebook:** {n(pagina.get('followers_count') or pagina.get('fan_count'))} seguidores da Página" if FB else "", ""]

    ate = int(dt.datetime.combine(hoje, dt.time()).timestamp())
    desde = ate - 7 * 86400
    ins = api(f"{IG}/insights", metric="reach,accounts_engaged,total_interactions,profile_views",
              period="day", metric_type="total_value", since=desde, until=ate)
    tot = {d["name"]: d.get("total_value", {}).get("value") for d in ins.get("data", [])}
    if tot:
        linhas += ["## Conta nos últimos 7 dias",
                   f"- Contas alcançadas: {n(tot.get('reach'))}",
                   f"- Contas com interação: {n(tot.get('accounts_engaged'))}",
                   f"- Interações totais: {n(tot.get('total_interactions'))}",
                   f"- Visitas ao perfil: {n(tot.get('profile_views'))}", ""]

    mapa = ids_dos_posts()
    midias = api(f"{IG}/media", fields="id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count",
                 limit=30).get("data", [])
    corte = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)
    posts = []
    for m in midias:
        quando = dt.datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
        if quando < corte:
            continue
        reel = m.get("media_product_type") == "REELS"
        met = "reach,saved,shares,total_interactions" + (",views" if reel else "")
        mi = {d["name"]: (d.get("values") or [{}])[0].get("value") for d in api(f"{m['id']}/insights", metric=met).get("data", [])}
        alc = mi.get("reach") or 0
        score = ((mi.get("saved") or 0) * 3 + (mi.get("shares") or 0) * 3 + (m.get("like_count") or 0) + (m.get("comments_count") or 0) * 2) / alc if alc else 0
        posts.append({"id": mapa.get(m["id"], "–"), "data": quando - dt.timedelta(hours=3), "tipo": "Reels" if reel else m["media_type"].title(),
                      "tema": (m.get("caption") or "").split("\n")[0][:60], "link": m.get("permalink"), "alc": alc,
                      "cur": m.get("like_count"), "com": m.get("comments_count"), "sal": mi.get("saved"),
                      "comp": mi.get("shares"), "views": mi.get("views"), "score": score})

    if posts:
        linhas += ["## Posts do feed (últimos 30 dias)", "",
                   "| Post | Data | Tipo | Tema | Alcance | Curtidas | Coment. | Salvos | Compart. |",
                   "|---|---|---|---|---|---|---|---|---|"]
        for p in sorted(posts, key=lambda p: p["data"], reverse=True):
            linhas.append(f"| [{p['id']}]({p['link']}) | {p['data']:%d/%m} | {p['tipo']} | {p['tema']} | {n(p['alc'])} | "
                          f"{n(p['cur'])} | {n(p['com'])} | {n(p['sal'])} | {n(p['comp'])} |")
        linhas += ["", "## Candidatos a turbinar",
                   "Melhor engajamento proporcional ao alcance (salvamentos e compartilhamentos pesam mais): conteúdo que já",
                   "funciona com o público orgânico e tende a render melhor quando pago.", ""]
        for p in sorted([p for p in posts if p["alc"] >= 20], key=lambda p: p["score"], reverse=True)[:3]:
            linhas.append(f"- **{p['id']}** – {p['tema']} ({p['data']:%d/%m}): alcance {n(p['alc'])}, "
                          f"{n(p['sal'])} salvos, {n(p['comp'])} compart. – {p['link']}")
        linhas.append("")
    else:
        linhas += ["Sem posts de feed nos últimos 30 dias com dados disponíveis.", ""]

    if avisos:
        linhas += ["## Avisos da API (para o Claude resolver)", *[f"- {a}" for a in avisos[:8]], ""]
    linhas.append(f"<!-- seguidores_ig={seg} -->")
    salvar(hoje, linhas)


def ler_anterior():
    try:
        t = open("relatorios/ultimo.md", encoding="utf-8").read()
        return int(t.split("seguidores_ig=")[1].split()[0])
    except Exception:
        return None


def salvar(hoje, linhas):
    os.makedirs("relatorios", exist_ok=True)
    txt = "\n".join(l for l in linhas if l is not None)
    for nome in (f"relatorios/{hoje:%Y-%m-%d}.md", "relatorios/ultimo.md"):
        open(nome, "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
