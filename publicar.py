"""
Publicador da Advocacia Soares.

Lê a FILA APROVADA (planilha espelho que só traz as linhas com APROVAR = Sim),
publica no Instagram e/ou Facebook os posts cuja data/hora já chegou e ainda
não foram publicados, e registra o resultado em status.csv (que a aba
PUBLICAÇÕES lê para mostrar o STATUS).

Configuração (GitHub > Settings > Secrets and variables > Actions):
  Secrets:   META_TOKEN       token de acesso (usuário do sistema / Página)
  Variables: FILA_ID          ID da planilha FILA APROVADA
             IG_USER_ID       ID da conta profissional do Instagram
             FB_PAGE_ID       ID da Página do Facebook
Sem META_TOKEN o script roda em modo simulação (não publica nada).
"""
import csv
import io
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image

TZ = ZoneInfo("America/Sao_Paulo")
GRAPH = "https://graph.facebook.com/v21.0"
REPO = os.environ.get("GITHUB_REPOSITORY", "jailson-rgb/publicacoes-soares")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
STATUS_CSV = "status.csv"
MIDIA = "midia"

TOKEN = os.environ.get("META_TOKEN", "").strip()
FILA_ID = os.environ.get("FILA_ID", "").strip() or "1hQb9oVOD9KMttygIky-4HqPcRznsmqVYJ8Wx5RFjveM"
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()
SIMULACAO = not TOKEN


def log(*a):
    print(datetime.now(TZ).strftime("%d/%m %H:%M"), *a, flush=True)


# ---------------------------------------------------------------- leitura
def baixar(url, tentativas=3):
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == tentativas - 1:
                raise
            log("falha ao baixar, tentando de novo:", e)
            time.sleep(5)


def ler_fila():
    url = f"https://docs.google.com/spreadsheets/d/{FILA_ID}/export?format=csv"
    linhas = list(csv.reader(io.StringIO(baixar(url).decode("utf-8"))))
    if not linhas:
        return []
    cab = [c.strip().upper() for c in linhas[0]]
    out = []
    for l in linhas[1:]:
        d = {cab[i]: (l[i].strip() if i < len(l) else "") for i in range(len(cab))}
        if d.get("ID") and not d["ID"].upper().startswith("JA"):  # IDs JA = Justo Acordo (outro repositório)
            out.append(d)
    return out


def ler_status():
    st = {}
    if os.path.exists(STATUS_CSV):
        with open(STATUS_CSV, encoding="utf-8") as f:
            for l in csv.reader(f):
                if l and l[0] != "ID":
                    st[l[0]] = l
    return st


def gravar_status(st):
    with open(STATUS_CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ID", "STATUS", "QUANDO", "DETALHE", "TENTATIVAS", "FEITO"])
        for k in sorted(st):
            w.writerow((st[k] + ["", "", "", "", "", ""])[:6])


def momento(post):
    data = post.get("DATA", "")
    hora = post.get("HORA", "") or "09:00"
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{data} {hora}", fmt).replace(tzinfo=TZ)
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------- mídia
def preparar_midia(post):
    """Baixa as artes do Drive e grava em midia/<ID>/: imagens viram JPEG; vídeos (MP4/MOV) ficam como .mp4."""
    ids = [x.strip() for x in post.get("ARQUIVOS (NÃO EDITAR)", post.get("ARQUIVOS", "")).replace(";", ",").split(",") if x.strip()]
    pasta = os.path.join(MIDIA, post["ID"])
    os.makedirs(pasta, exist_ok=True)
    caminhos = []
    for n, fid in enumerate(ids, 1):
        bruto = baixar(f"https://drive.google.com/uc?export=download&id={fid}")
        if bruto[:200].lstrip().lower().startswith(b"<!doctype html") or bruto[:200].lstrip().lower().startswith(b"<html"):
            # arquivo grande (vídeo): o Drive pede confirmação; este endereço baixa direto
            bruto = baixar(f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t")
        if eh_video(bruto):
            p = os.path.join(pasta, f"{n:02d}.mp4")
            with open(p, "wb") as f:
                f.write(bruto)
        else:
            img = Image.open(io.BytesIO(bruto)).convert("RGB")
            p = os.path.join(pasta, f"{n:02d}.jpg")
            img.save(p, "JPEG", quality=92)
        caminhos.append(p)
    return caminhos


def eh_video(bruto):
    return bruto[4:8] == b"ftyp"


def publicar_no_github(caminhos, post_id):
    """Sobe as imagens ao repositório para terem um endereço público."""
    subprocess.run(["git", "add", *caminhos], check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0:
        subprocess.run(["git", "commit", "-m", f"midia do post {post_id}"], check=True)
        subprocess.run(["git", "push"], check=True)
        time.sleep(20)  # dá tempo do endereço público ficar disponível
    return [f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{urllib.parse.quote(c)}" for c in caminhos]


# ---------------------------------------------------------------- Meta API
def api(metodo, caminho, **params):
    params["access_token"] = TOKEN
    dados = urllib.parse.urlencode(params).encode()
    url = f"{GRAPH}/{caminho}"
    if metodo == "GET":
        req = urllib.request.Request(url + "?" + dados.decode())
    else:
        req = urllib.request.Request(url, data=dados, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Meta API {caminho}: {e.read().decode()[:400]}") from None


def aguardar_container(cid, tentativas=30):
    for _ in range(tentativas):
        st = api("GET", cid, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st == "ERROR":
            raise RuntimeError(f"container {cid} com erro")
        time.sleep(5)


def instagram(tipo, urls, legenda):
    if urls[0].endswith(".mp4"):
        # vídeo próprio (animação ou fala do Jailson): publicado como Reels, também no feed
        c = api("POST", f"{IG_USER_ID}/media", media_type="REELS", video_url=urls[0], caption=legenda, share_to_feed="true")["id"]
        aguardar_container(c, 120)  # vídeo leva alguns minutos para processar
        return [api("POST", f"{IG_USER_ID}/media_publish", creation_id=c)["id"]]
    if tipo == "Story":
        ids = []
        for u in urls:
            c = api("POST", f"{IG_USER_ID}/media", image_url=u, media_type="STORIES")["id"]
            aguardar_container(c)
            ids.append(api("POST", f"{IG_USER_ID}/media_publish", creation_id=c)["id"])
        return ids
    if len(urls) == 1:
        c = api("POST", f"{IG_USER_ID}/media", image_url=urls[0], caption=legenda)["id"]
    else:
        filhos = []
        for u in urls[:10]:
            f = api("POST", f"{IG_USER_ID}/media", image_url=u, is_carousel_item="true")["id"]
            aguardar_container(f)
            filhos.append(f)
        c = api("POST", f"{IG_USER_ID}/media", media_type="CAROUSEL", children=",".join(filhos), caption=legenda)["id"]
    aguardar_container(c)
    return [api("POST", f"{IG_USER_ID}/media_publish", creation_id=c)["id"]]


def page_token():
    return api("GET", FB_PAGE_ID, fields="access_token").get("access_token", TOKEN)


def facebook(tipo, urls, legenda):
    global TOKEN
    original, TOKEN = TOKEN, page_token()
    try:
        if urls[0].endswith(".mp4"):
            return [api("POST", f"{FB_PAGE_ID}/videos", file_url=urls[0], description=legenda)["id"]]
        if tipo == "Story":
            ids = []
            for u in urls:
                foto = api("POST", f"{FB_PAGE_ID}/photos", url=u, published="false")["id"]
                ids.append(api("POST", f"{FB_PAGE_ID}/photo_stories", photo_id=foto).get("post_id", foto))
            return ids
        if len(urls) == 1:
            return [api("POST", f"{FB_PAGE_ID}/photos", url=urls[0], message=legenda)["id"]]
        fotos = [api("POST", f"{FB_PAGE_ID}/photos", url=u, published="false")["id"] for u in urls]
        anexos = {f"attached_media[{i}]": json.dumps({"media_fbid": f}) for i, f in enumerate(fotos)}
        return [api("POST", f"{FB_PAGE_ID}/feed", message=legenda, **anexos)["id"]]
    finally:
        TOKEN = original


# ---------------------------------------------------------------- principal
def descobrir_ids():
    """Se IG_USER_ID / FB_PAGE_ID não foram configurados, descobre pelo token."""
    global IG_USER_ID, FB_PAGE_ID
    if SIMULACAO or (IG_USER_ID and FB_PAGE_ID):
        return
    paginas = api("GET", "me/accounts", fields="id,name,instagram_business_account").get("data", [])
    if not paginas:
        raise SystemExit("O token não dá acesso a nenhuma Página do Facebook.")
    pag = next((p for p in paginas if "soares" in p.get("name", "").lower()), paginas[0])
    FB_PAGE_ID = FB_PAGE_ID or pag["id"]
    IG_USER_ID = IG_USER_ID or pag.get("instagram_business_account", {}).get("id", "")
    log(f"Página: {pag.get('name')} ({FB_PAGE_ID}) · Instagram: {IG_USER_ID or 'não vinculado'}")


def main():
    descobrir_ids()
    if not FILA_ID:
        sys.exit("FILA_ID não configurado.")
    agora = datetime.now(TZ)
    erros = []
    status = ler_status()
    fila = ler_fila()
    # ordem cronológica: garante a sequência certa dos 3 posts de um mosaico (direita, meio, esquerda)
    fila.sort(key=lambda p: momento(p) or agora)
    log(f"{len(fila)} post(s) aprovados na fila; modo {'SIMULAÇÃO' if SIMULACAO else 'PUBLICAÇÃO'}")
    mudou = False
    for post in fila:
        pid = post["ID"]
        ant = (status.get(pid, []) + ["", "", "", "", "0", ""])[:6]
        if ant[1] == "Publicado":
            continue
        tentativas = int(ant[4] or 0)
        if ant[1] == "Erro" and tentativas >= 3:
            continue  # desiste após 3 tentativas; o erro fica visível no STATUS
        quando = momento(post)
        if not quando:
            status[pid] = [pid, "Erro", agora.strftime("%d/%m/%Y %H:%M"), "Data/hora inválida", "3", ""]
            mudou = True
            continue
        if quando > agora:
            if ant[1] != "Agendado" or ant[2] != quando.strftime("%d/%m/%Y %H:%M"):
                status[pid] = [pid, "Agendado", quando.strftime("%d/%m/%Y %H:%M"), "", "0", ""]
                mudou = True
            continue
        tipo = post.get("TIPO", "Carrossel")
        if post.get("DESTINO", "") == "LinkedIn":
            # LinkedIn (texto) é publicado pelo Claude no navegador, depois da aprovação; aqui só sinaliza
            if ant[1] not in ("LinkedIn", "Publicado"):
                status[pid] = [pid, "LinkedIn", agora.strftime("%d/%m/%Y %H:%M"), "Publicação no LinkedIn pelo navegador", "0", ""]
                mudou = True
            continue
        if tipo == "Reels":
            # (TIPO "Vídeo" = vídeo próprio, publicado automaticamente como Reels)
            # Reels de trend usam áudio da biblioteca do Instagram: publicação manual pelo app
            if ant[1] != "Manual":
                status[pid] = [pid, "Manual", agora.strftime("%d/%m/%Y %H:%M"), "Publicar pelo app do celular (áudio da trend)", "0", ""]
                mudou = True
            continue
        destino = post.get("DESTINO", "Instagram + Facebook")
        legenda = post.get("LEGENDA", "")
        feito = ant[5]
        det = [ant[3]] if feito else []
        log(f"publicando {pid} ({tipo} -> {destino})")
        mudou = True
        try:
            caminhos = preparar_midia(post)
            if not caminhos:
                raise RuntimeError("nenhuma imagem em ARQUIVOS")
            if SIMULACAO:
                status[pid] = [pid, "Simulado", agora.strftime("%d/%m/%Y %H:%M"), f"{len(caminhos)} imagem(ns) prontas", "0", ""]
                continue
            urls = publicar_no_github(caminhos, pid)
            if "Instagram" in destino and "IG" not in feito:
                det.append("IG " + ",".join(instagram(tipo, urls, legenda)))
                feito += "IG"
                status[pid] = [pid, "Parcial", agora.strftime("%d/%m/%Y %H:%M"), " | ".join(det), str(tentativas), feito]
                gravar_status(status)
            if "Facebook" in destino and "FB" not in feito:
                det.append("FB " + ",".join(facebook(tipo, urls, legenda)))
                feito += "FB"
            status[pid] = [pid, "Publicado", datetime.now(TZ).strftime("%d/%m/%Y %H:%M"), " | ".join(det), str(tentativas), feito]
        except Exception as e:  # noqa: BLE001
            log("ERRO:", e)
            erros.append(pid)
            status[pid] = [pid, "Erro", agora.strftime("%d/%m/%Y %H:%M"), (" | ".join(det) + " | " if det else "") + str(e)[:300], str(tentativas + 1), feito]
    if mudou:
        gravar_status(status)
    log("fim")
    if erros:
        # falha o job de propósito: o GitHub avisa o Jailson por e-mail
        raise SystemExit(f"Erro ao publicar: {', '.join(erros)} (ver coluna STATUS)")


if __name__ == "__main__":
    main()
