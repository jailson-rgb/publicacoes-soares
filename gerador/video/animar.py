"""Renderiza uma animação HTML (CSS animations) em MP4 vertical 1080x1920 para Reels.

Uso:
  python gerador/video/animar.py modelo.html saida.mp4 [segundos] [variacao_trilha]
      VÍDEO ANIMADO: só motion graphics. Sempre com a trilha instrumental original da marca
      (gerador/video/trilha.py); variacao_trilha (0, 1, 2) alterna a progressão; "-1" = sem trilha.
  python gerador/video/animar.py modelo.html saida.mp4 --sobre video_do_jailson.mp4 [variacao_trilha]
      VÍDEO DO JAILSON + INTERVENÇÕES ILUSTRATIVAS: a animação (fundo transparente) entra por cima do vídeo
      gravado por ele. A duração e o áudio são os do vídeo; a trilha entra bem baixa (cerca de -24 dB) sob a voz.
      O vídeo é ajustado para 1080x1920 (corta as sobras). No modelo, a variável CSS --fim recebe (duração − 3 s),
      para o encerramento com o logo entrar sozinho no fim. Modelo: gerador/video/modelo-sobreposicao.html.

O HTML precisa ter um elemento #r de 1080x1920; as animações CSS são congeladas e avançadas quadro a quadro."""
import os
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright

args = sys.argv[1:]
sobre = None
if "--sobre" in args:
    i = args.index("--sobre"); sobre = args[i + 1]; del args[i:i + 2]
src, out = args[0], args[1]
FPS = 30


def duracao(v):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


if sobre:
    DUR = duracao(sobre)
    VAR = int(args[2]) if len(args) > 2 else 0
else:
    DUR = float(args[2]) if len(args) > 2 else 10.5
    VAR = int(args[3]) if len(args) > 3 else 0

tmp = tempfile.mkdtemp()
with sync_playwright() as pw:
    kw = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
    b = pw.chromium.launch(args=["--allow-file-access-from-files"], **kw)
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + os.path.abspath(src))
    pg.evaluate(f"document.documentElement.style.setProperty('--fim', '{max(DUR - 3, 0):.2f}s')")
    if sobre:
        pg.add_style_tag(content="html,body,#r{background:transparent!important}")
    pg.evaluate("document.fonts.ready.then(()=>1)")
    pg.wait_for_timeout(300)
    pg.evaluate("document.getAnimations().forEach(a=>a.pause())")
    for i in range(int(FPS * DUR)):
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={i * 1000 / FPS})")
        pg.locator("#r").screenshot(path=f"{tmp}/{i:04d}.png", omit_background=bool(sobre))
    b.close()

trilha_wav = None
if VAR >= 0:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import trilha
    trilha_wav = f"{tmp}/trilha.wav"
    trilha.salvar(trilha_wav, trilha.gerar(DUR, VAR))

enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
if sobre:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", sobre, "-framerate", str(FPS), "-i", f"{tmp}/%04d.png"]
    filtro = ("[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1[b];"
              "[b][1:v]overlay=0:0:eof_action=pass[v]")
    if trilha_wav:
        cmd += ["-i", trilha_wav]
        filtro += ";[2:a]volume=-24dB[t];[0:a][t]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]"
        mapa = ["-map", "[v]", "-map", "[a]"]
    else:
        mapa = ["-map", "[v]", "-map", "0:a?"]
    cmd += ["-filter_complex", filtro, *mapa, *enc, "-c:a", "aac", "-b:a", "160k", "-t", f"{DUR:.3f}", out]
else:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/%04d.png"]
    if trilha_wav:
        cmd += ["-i", trilha_wav, "-c:a", "aac", "-b:a", "160k", "-shortest"]
    cmd += [*enc, out]
subprocess.run(cmd, check=True)
print(out)
