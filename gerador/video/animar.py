"""Renderiza uma animação HTML (CSS animations) em MP4 vertical 1080x1920 para Reels.
Uso: python gerador/video/animar.py modelo.html saida.mp4 [segundos]
O HTML precisa ter um elemento #r de 1080x1920; as animações CSS são congeladas e avançadas quadro a quadro."""
import os, subprocess, sys, tempfile
from playwright.sync_api import sync_playwright

src, out = sys.argv[1], sys.argv[2]
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 10.5
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
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{tmp}/%04d.png", "-c:v", "libx264",
                "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], check=True)
print(out)
