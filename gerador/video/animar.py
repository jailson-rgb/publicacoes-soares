"""Renderiza uma animação HTML (CSS animations) em MP4 vertical 1080x1920 para Reels.
Uso: python gerador/video/animar.py modelo.html saida.mp4 [segundos] [variacao_trilha]
Sempre coloca a trilha instrumental original da marca (gerador/video/trilha.py); variacao_trilha (0, 1, 2) alterna
a progressão de acordes entre os vídeos. Use "-1" para sair sem trilha.
O HTML precisa ter um elemento #r de 1080x1920; as animações CSS são congeladas e avançadas quadro a quadro."""
import os, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

src, out = sys.argv[1], sys.argv[2]
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 10.5
VAR = int(sys.argv[4]) if len(sys.argv) > 4 else 0
FPS = 30
tmp = tempfile.mkdtemp()
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--allow-file-access-from-files"])
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto("file://" + os.path.abspath(src))
    pg.evaluate("document.fonts.ready.then(()=>1)")
    pg.wait_for_timeout(300)
    pg.evaluate("document.getAnimations().forEach(a=>a.pause())")
    for i in range(int(FPS * DUR)):
        pg.evaluate(f"document.getAnimations().forEach(a=>a.currentTime={i * 1000 / FPS})")
        pg.locator("#r").screenshot(path=f"{tmp}/{i:04d}.png")
    b.close()
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/%04d.png"]
if VAR >= 0:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import trilha
    trilha.salvar(f"{tmp}/trilha.wav", trilha.gerar(DUR, VAR))
    cmd += ["-i", f"{tmp}/trilha.wav", "-c:a", "aac", "-b:a", "160k", "-shortest"]
cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
subprocess.run(cmd, check=True)
print(out)
