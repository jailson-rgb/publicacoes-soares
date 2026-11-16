#!/usr/bin/env python3
"""Corta pausas longas (e trechos indicados) do vídeo bruto do Jailson antes das intervenções.

Uso:
  python gerador/video/cortar.py bruto.mp4 cortado.mp4 [--pausa 0.7] [--respiro 0.25]
         [--limiar -35] [--cortar "0:42-0:45,1:10.5-1:12"]

- Pausas: trechos de silêncio maiores que --pausa (s) viram um respiro de --respiro (s).
- --cortar: trechos extras a remover (gaguejos, frases recomeçadas), em m:ss ou segundos,
  vindos da transcrição com tempo ou indicados pelo Jailson.
- Gera também cortado.txt com a lista do que foi removido (para mandar junto na aprovação).
"""
import argparse, re, subprocess, sys


def ts(s):
    s = s.strip()
    if ":" in s:
        m, sec = s.split(":", 1)
        return int(m) * 60 + float(sec)
    return float(s)


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def duracao(arq):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", arq], capture_output=True, text=True).stdout
    return float(out.strip())


def silencios(arq, limiar, minimo):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", arq, "-af",
                          f"silencedetect=noise={limiar}dB:d={minimo}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(ini, fim))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada"); ap.add_argument("saida")
    ap.add_argument("--pausa", type=float, default=0.7)
    ap.add_argument("--respiro", type=float, default=0.25)
    ap.add_argument("--limiar", type=float, default=-35)
    ap.add_argument("--cortar", default="")
    a = ap.parse_args()

    dur = duracao(a.entrada)
    remover = []
    for s, e in silencios(a.entrada, a.limiar, a.pausa):
        meio = a.respiro / 2
        if e - s > a.respiro:
            remover.append((s + meio, e - meio, "pausa"))
    for trecho in filter(None, a.cortar.split(",")):
        s, e = trecho.split("-")
        remover.append((ts(s), ts(e), "trecho indicado"))
    remover.sort()

    # junta sobreposições e monta os trechos que ficam
    juntos = []
    for s, e, m in remover:
        if juntos and s <= juntos[-1][1]:
            juntos[-1] = (juntos[-1][0], max(e, juntos[-1][1]), juntos[-1][2])
        else:
            juntos.append((max(0, s), min(dur, e), m))
    manter, pos = [], 0.0
    for s, e, _ in juntos:
        if s > pos:
            manter.append((pos, s))
        pos = max(pos, e)
    if pos < dur:
        manter.append((pos, dur))
    if not manter:
        sys.exit("Nada sobrou após os cortes; revise os parâmetros.")

    partes = []
    for i, (s, e) in enumerate(manter):
        partes.append(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS[v{i}];"
                      f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.02,afade=t=out:st={max(0, e - s - 0.02)}:d=0.02[a{i}];")
    concat = "".join(f"[v{i}][a{i}]" for i in range(len(manter)))
    filtro = "".join(partes) + f"{concat}concat=n={len(manter)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.entrada,
                    "-filter_complex", filtro, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", a.saida], check=True)

    novo = duracao(a.saida)
    rel = a.saida.rsplit(".", 1)[0] + ".txt"
    with open(rel, "w") as f:
        f.write(f"Original: {fmt(dur)}  ->  Cortado: {fmt(novo)}  ({len(juntos)} cortes)\n")
        for s, e, m in juntos:
            f.write(f"- {fmt(s)} a {fmt(e)} ({e - s:.1f} s) – {m}\n")
    print(open(rel).read())


if __name__ == "__main__":
    main()
