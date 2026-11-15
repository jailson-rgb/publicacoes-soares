"""Gera a trilha instrumental da Advocacia Soares (composição original, sem direitos de terceiros).

Persona: escritório empresarial sóbrio, confiável e moderno -> andamento calmo (84 bpm), acordes quentes em
tom menor/maior suave, piano em arpejo discreto, pulso grave leve. Nada de batida agitada.
Uso: python gerador/video/trilha.py saida.wav [segundos] [variacao]
"variacao" (0, 1, 2...) troca a progressão de acordes, para os vídeos não soarem sempre iguais.
"""
import sys
import wave

import numpy as np

SR = 44100
BPM = 84
BEAT = 60 / BPM

PROGRESSOES = [
    [("A3", "C4", "E4", "G4"), ("F3", "A3", "C4", "E4"), ("C3", "E3", "G3", "B3"), ("G3", "B3", "D4", "F#4")],
    [("D3", "F3", "A3", "C4"), ("Bb2", "D3", "F3", "A3"), ("F3", "A3", "C4", "E4"), ("C3", "E3", "G3", "Bb3")],
    [("E3", "G3", "B3", "D4"), ("C3", "E3", "G3", "B3"), ("G3", "B3", "D4", "F#4"), ("D3", "F#3", "A3", "C#4")],
]
NOTAS = {"C": -9, "C#": -8, "D": -7, "Eb": -6, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "Ab": -1,
         "A": 0, "Bb": 1, "A#": 1, "B": 2}


def freq(n):
    nome, oit = n[:-1], int(n[-1])
    return 440.0 * 2 ** ((NOTAS[nome] + 12 * (oit - 4)) / 12)


def env(n, a, r):
    e = np.ones(n)
    a, r = int(a * SR), int(r * SR)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def pad(f, dur):
    t = np.arange(int(dur * SR)) / SR
    s = sum(np.sin(2 * np.pi * f * d * t) for d in (0.997, 1.0, 1.003)) / 3
    s += 0.25 * np.sin(2 * np.pi * f * 2 * t)
    return s * env(len(t), 1.2, 1.5)


def piano(f, dur):
    t = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) + 0.15 * np.sin(2 * np.pi * 3 * f * t)
    return s * np.exp(-3.2 * t) * env(len(t), 0.005, 0.2)


def baixo(f, dur):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * f / 2 * t) * np.exp(-2.0 * t) * env(len(t), 0.01, 0.3)


def gerar(segundos=30.0, variacao=0):
    prog = PROGRESSOES[variacao % len(PROGRESSOES)]
    total = int(segundos * SR) + SR
    out = np.zeros(total)
    compasso = 4 * BEAT
    pos, i = 0.0, 0
    while pos < segundos:
        acorde = prog[i % len(prog)]
        a = int(pos * SR)
        for n in acorde:
            p = pad(freq(n), compasso + 1.5) * 0.10
            out[a:a + len(p)] += p[:max(0, total - a)]
        b = baixo(freq(acorde[0]), compasso) * 0.22
        out[a:a + len(b)] += b[:max(0, total - a)]
        for k in range(8):  # arpejo em colcheias
            n = acorde[[0, 1, 2, 3, 2, 1, 2, 3][k]]
            f = freq(n) * 2
            st = int((pos + k * BEAT / 2) * SR)
            if st >= total:
                break
            p = piano(f, 1.6) * (0.10 if k % 2 == 0 else 0.07)
            out[st:st + len(p)] += p[:max(0, total - st)]
        pos += compasso
        i += 1
    # eco curto (espaço) + normalização + fade
    eco = np.zeros_like(out)
    d = int(0.28 * SR)
    eco[d:] = out[:-d] * 0.25
    out = (out + eco)[:int(segundos * SR)]
    out *= env(len(out), min(1.0, segundos / 4), min(2.5, segundos / 3))
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.5
    return out


def salvar(caminho, sinal):
    estereo = np.stack([sinal, np.roll(sinal, int(0.012 * SR))], axis=1)
    with wave.open(caminho, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((estereo * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    seg = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    var = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    salvar(sys.argv[1], gerar(seg, var))
    print(sys.argv[1])
