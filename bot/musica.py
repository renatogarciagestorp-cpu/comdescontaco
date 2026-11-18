"""Gera trilhas instrumentais ORIGINAIS (sem direitos autorais de terceiros) para os Reels.

Uso: python -m bot.musica   → cria assets/audio/trilha_*.mp3
Para usar músicas próprias, basta colocar outros .mp3 livres de direitos na mesma pasta.
"""
import shutil
import subprocess
from pathlib import Path

import numpy as np

SR = 48000
RAIZ = Path(__file__).resolve().parent.parent
AUDIO = RAIZ / "assets" / "audio"

NOTAS = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def _ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def freq(nota, oitava):
    return 440.0 * 2 ** ((NOTAS[nota] + 12 * (oitava - 4) - 9) / 12)


def env(n, ataque=0.01, decaimento=0.4):
    t = np.arange(n) / SR
    a = np.clip(t / ataque, 0, 1)
    return a * np.exp(-t / decaimento)


def piano(f, dur, vol=0.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    onda = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.6 for k in (1, 2, 3, 4))
    return vol * onda * env(n, 0.005, 0.6)


def baixo(f, dur, vol=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return vol * (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t)) * env(n, 0.005, 0.35)


def bumbo(vol=0.9):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-t * 25) + 45
    return vol * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def palma(rng, vol=0.35):
    n = int(0.2 * SR)
    ruido = rng.standard_normal(n)
    ruido = np.convolve(ruido, [1, -1], "same")  # tira os graves
    return vol * ruido * env(n, 0.002, 0.06)


def chimbal(rng, vol=0.12):
    n = int(0.06 * SR)
    ruido = np.diff(rng.standard_normal(n + 1))
    return vol * ruido * env(n, 0.001, 0.015)


def colocar(faixa, som, inicio):
    i = int(inicio * SR)
    fim = min(len(faixa), i + len(som))
    faixa[i:fim] += som[:fim - i]


def compor(bpm, acordes, semente, compassos=8):
    rng = np.random.default_rng(semente)
    batida = 60 / bpm
    dur = compassos * 4 * batida
    faixa = np.zeros(int(dur * SR) + SR)
    for c in range(compassos):
        raiz, tipo = acordes[c % len(acordes)]
        base = NOTAS[raiz]
        terca = 3 if tipo == "m" else 4
        notas = [base, base + terca, base + 7, base + 12]
        t0 = c * 4 * batida
        # acordes "picados" (ritmo pop) e arpejo
        for b in (0, 1.5, 2.5, 3.5):
            for k, nn in enumerate(notas[:3]):
                nome = list(NOTAS)[nn % 12]
                colocar(faixa, piano(freq(nome, 4 + nn // 12), batida * 1.2, 0.07), t0 + b * batida + k * 0.004)
        for i in range(8):
            nn = notas[[0, 2, 1, 3, 2, 1, 3, 2][i]]
            nome = list(NOTAS)[nn % 12]
            colocar(faixa, piano(freq(nome, 5 + nn // 12), batida * 0.6, 0.05), t0 + i * batida / 2)
        # baixo
        nome = list(NOTAS)[base]
        for b in (0, 1.5, 2, 3.5):
            colocar(faixa, baixo(freq(nome, 2), batida * 0.9), t0 + b * batida)
        # bateria
        for b in (0, 2, 2.5):
            colocar(faixa, bumbo(), t0 + b * batida)
        for b in (1, 3):
            colocar(faixa, palma(rng), t0 + b * batida)
        for i in range(8):
            colocar(faixa, chimbal(rng, 0.12 if i % 2 else 0.07), t0 + i * batida / 2)
    faixa = faixa[: int(dur * SR)]
    faixa = np.tanh(faixa * 1.4)  # saturação leve, deixa mais "cheio"
    faixa *= 0.7 / np.max(np.abs(faixa))
    return faixa


def salvar_mp3(faixa, nome):
    AUDIO.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(faixa, -1, 1) * 32767).astype(np.int16)
    estereo = np.stack([pcm, pcm], axis=1).tobytes()
    saida = AUDIO / nome
    subprocess.run([_ffmpeg(), "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR), "-ac", "2",
                    "-i", "-", "-c:a", "libmp3lame", "-b:a", "192k", str(saida)], input=estereo, check=True)
    return saida


TRILHAS = {
    "trilha_animada.mp3": (118, [("C", ""), ("G", ""), ("A", "m"), ("F", "")], 1),
    "trilha_ensolarada.mp3": (112, [("D", ""), ("A", ""), ("B", "m"), ("G", "")], 2),
    "trilha_urbana.mp3": (100, [("A", "m"), ("F", ""), ("C", ""), ("G", "")], 3),
}


def main():
    for nome, (bpm, acordes, semente) in TRILHAS.items():
        print("criada:", salvar_mp3(compor(bpm, acordes, semente), nome))


if __name__ == "__main__":
    main()
