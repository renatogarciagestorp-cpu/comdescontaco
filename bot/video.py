"""Gera Reels animados (1080x1920, 30 fps, MP4 H.264 + AAC) para o Instagram.

Neurodesign em movimento:
- Gancho nos primeiros 0,5 s (título entra com impacto): segura o polegar no feed.
- Um elemento novo a cada ~1 s: o cérebro espera o próximo e não pula o vídeo.
- Preço "caindo" do valor antigo até o novo: a sensação de perda e de ganho vista na hora.
- Fim com chamada clara (comente QUERO / siga) pulsando: um único próximo passo.

Música: coloque arquivos .mp3 livres de direitos em assets/audio/ (ex.: Biblioteca de Áudio do
YouTube). Sem eles, o vídeo sai com áudio silencioso, como a API exige.
"""
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from .art import _baixar, _font, _quebrar, ajustar, brl, mil

RAIZ = Path(__file__).resolve().parent.parent
AUDIO = RAIZ / "assets" / "audio"
VW, VH, FPS = 1080, 1920, 30
S = 2  # camadas desenhadas em 2x e reduzidas = bordas suaves


# ---------------- utilidades de animação ----------------
def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_back(t):  # passa um pouco do ponto e volta (efeito "pop")
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def prog(t, inicio, dur):
    return max(0.0, min(1.0, (t - inicio) / dur))


def camada(w, h, desenhar):
    """Cria uma camada RGBA desenhada em 2x (coordenadas em 1x) e reduzida."""
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    desenhar(ImageDraw.Draw(big), lambda v: int(round(v * S)))
    return big.resize((w, h), Image.LANCZOS)


def colar(base, lay, x, y, alpha=1.0, escala=1.0, rot=0.0):
    """Cola a camada com o centro em (x, y)."""
    if alpha <= 0.01 or escala <= 0.01:
        return
    im = lay
    if escala != 1.0:
        im = im.resize((max(1, int(im.width * escala)), max(1, int(im.height * escala))), Image.BILINEAR)
    if rot:
        im = im.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    base.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)


def fundo(c):
    a, b = Image.new("RGB", (VW, VH), c["fundo"]), Image.new("RGB", (VW, VH), c["fundo2"])
    img = Image.composite(b, a, Image.linear_gradient("L").resize((VW, VH)))
    glow = Image.new("L", (VW, VH), 0)
    ImageDraw.Draw(glow).ellipse((90, 500, 990, 1400), fill=110)
    glow = glow.filter(ImageFilter.GaussianBlur(140))
    return Image.composite(Image.new("RGB", (VW, VH), c["fundo2"]), img, glow)


# ---------------- camadas reutilizáveis ----------------
def cab_marca(cfg):
    c = cfg["cores"]

    def d_(d, z):
        h = 64
        w = h * 0.6
        x, y = 0, 0
        pts = [(x + w * .55, y), (x, y + h * .58), (x + w * .45, y + h * .58),
               (x + w * .3, y + h), (x + w, y + h * .38), (x + w * .55, y + h * .38)]
        d.polygon([(z(px), z(py)) for px, py in pts], fill=c["destaque"])
        d.text((z(52), z(32)), cfg["canal"]["nome"], font=_font(900, 46), fill=c["texto"], anchor="lm")
    return camada(560, 70, d_)


def etiqueta(cfg, texto, cor=None):
    c = cfg["cores"]
    f = _font(900, 30)
    w = int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(texto, font=f) / S + 60)

    def d_(d, z):
        d.rounded_rectangle((0, 0, z(w), z(60)), radius=z(30), fill=cor or c["alerta"])
        d.text((z(w / 2), z(30)), texto, font=f, fill="#FFFFFF", anchor="mm")
    return camada(w, 60, d_)


def linha_texto(texto, tam, cor, peso=900, largura=VW - 120):
    f = _font(peso, tam)
    w = int(min(largura, ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(texto, font=f) / S + 10))

    def d_(d, z):
        d.text((z(w / 2), z(tam * 0.62)), texto, font=f, fill=cor, anchor="mm")
    return camada(w, int(tam * 1.25), d_)


def ajustar_tam(linhas, maximo, largura=VW - 120):
    tam = maximo
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while tam > 40 and max(d.textlength(l, font=_font(900, tam)) for l in linhas) / S > largura:
        tam -= 2
    return tam


def paragrafo(texto, tam, cor, largura=VW - 140, max_linhas=5):
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    linhas = _quebrar(d0, texto, _font(800, tam), int(largura * S), max_linhas)
    h = int(len(linhas) * tam * 1.4 + 10)

    def d_(d, z):
        for i, l in enumerate(linhas):
            d.text((z(largura / 2), z(tam * 0.7 + i * tam * 1.4)), l, font=_font(800, tam), fill=cor, anchor="mm")
    return camada(largura, h, d_)


def cartao_item(cfg, numero, titulo, sub, cor_num=None, h=150):
    c = cfg["cores"]
    w = VW - 120
    m = h / 2

    def d_(d, z):
        d.rounded_rectangle((0, 0, z(w), z(h)), radius=z(34), fill="#FFFFFF")
        d.ellipse((z(28), z(m - 44), z(116), z(m + 44)), fill=cor_num or c["alerta"])
        d.text((z(72), z(m)), numero, font=_font(900, 44), fill="#FFFFFF", anchor="mm")
        d.text((z(144), z(m - 22)), titulo, font=_font(900, 36), fill=c["fundo"], anchor="lm")
        d.text((z(144), z(m + 26)), sub, font=_font(800, 25), fill="#5B5470", anchor="lm")
    return camada(w, h, d_)


def botao(cfg, texto):
    c = cfg["cores"]
    w, h = VW - 120, 120
    tam = 44
    d0 = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while d0.textlength(texto, font=_font(900, tam)) / S > w - 80 and tam > 26:
        tam -= 1

    def d_(d, z):
        d.rounded_rectangle((0, 0, z(w), z(h)), radius=z(60), fill=c["destaque"])
        d.text((z(w / 2), z(h / 2)), texto, font=_font(900, tam), fill=c["fundo"], anchor="mm")
    return camada(w, h, d_)


# ---------------- roteiros ----------------
class Roteiro:
    """Lista de elementos com animação; desenha cada quadro do vídeo."""

    def __init__(self, cfg, duracao):
        self.cfg, self.duracao, self.itens = cfg, duracao, []
        self.bg = fundo(cfg["cores"])

    def add(self, lay, x, y, inicio, tipo="sobe", dur=0.45, pulso=False):
        self.itens.append(dict(lay=lay, x=x, y=y, ini=inicio, tipo=tipo, dur=dur, pulso=pulso))

    def quadro(self, t):
        img = self.bg.copy()
        for e in self.itens:
            p = prog(t, e["ini"], e["dur"])
            if p <= 0:
                continue
            x, y, a, s = e["x"], e["y"], ease_out(p), 1.0
            if e["tipo"] == "sobe":
                y += (1 - ease_out(p)) * 80
            elif e["tipo"] == "direita":
                x += (1 - ease_out(p)) * VW
            elif e["tipo"] == "pop":
                s = max(0.01, ease_back(p))
            elif e["tipo"] == "impacto":  # entra grande e "bate" no lugar
                s = 1 + (1 - ease_out(p)) * 1.2
            if e["pulso"] and p >= 1:
                s *= 1 + 0.04 * math.sin((t - e["ini"]) * 6)
            colar(img, e["lay"], x, y, a, s)
        return img


def roteiro_conteudo(cfg, post, dias=None):
    c = cfg["cores"]
    tipo = post["tipo"]
    r = Roteiro(cfg, 0)
    r.add(cab_marca(cfg), 330, 250, 0.0, "sobe", 0.3)
    r.add(etiqueta(cfg, post["etiqueta"]), VW / 2, 345, 0.1, "pop", 0.4)

    if tipo == "contagem":
        r.add(linha_texto("FALTAM", 80, c["texto"]), VW / 2, 500, 0.2, "sobe")
        r.add(linha_texto(str(dias), 440, c["destaque"]), VW / 2, 800, 0.5, "impacto", 0.35)
        r.add(linha_texto("DIA" if dias == 1 else "DIAS", 110, c["texto"]), VW / 2, 1075, 1.1, "sobe")
        r.add(linha_texto(f"PARA A {post['evento']}", 64, c["alerta"]), VW / 2, 1180, 1.4, "sobe")
        r.add(paragrafo(post["texto"], 38, c["suave"]), VW / 2, 1340, 2.0, "sobe", 0.6)
        fim = 3.2
    else:
        linhas = post["titulo"]
        tam = ajustar_tam(linhas, 120 if tipo == "texto" else 100)
        y = 480
        for i, l in enumerate(linhas):
            cor = c["destaque"] if i in post.get("destaque", []) else c["texto"]
            r.add(linha_texto(l, tam, cor), VW / 2, y, 0.25 + 0.18 * i, "impacto" if i == 0 else "sobe", 0.35)
            y += tam * 1.1
        if tipo == "lista":
            y += 30
            t0 = 1.2
            n = len(post["itens"])
            alto = 150 if n <= 4 else 128
            for i, (tt, ss) in enumerate(post["itens"], 1):
                r.add(cartao_item(cfg, str(i), tt, ss, h=alto), VW / 2, y + alto / 2, t0, "direita", 0.45)
                y += alto + 14
                t0 += 1.1
            fim = t0 + 0.3
        else:
            r.add(paragrafo(post["texto"], 42, c["suave"]), VW / 2, y + 170, 1.2, "sobe", 0.6)
            fim = 3.4

    r.add(botao(cfg, post["cta"]), VW / 2, 1530, fim, "pop", 0.5, pulso=True)
    r.add(linha_texto(f"SIGA {cfg['canal']['arroba_instagram']}", 40, c["texto"], 800), VW / 2, 1640, fim + 0.4, "sobe")
    r.duracao = fim + 3.0  # tempo para ler a chamada
    return r


def roteiro_oferta(cfg, p):
    """Reel de oferta: produto + preço caindo do antigo para o novo + 'comente QUERO'."""
    c = cfg["cores"]
    r = Roteiro(cfg, 7.5)
    r.add(cab_marca(cfg), 330, 250, 0.0, "sobe", 0.3)
    relampago = p.desconto >= 50
    r.add(etiqueta(cfg, "OFERTA RELÂMPAGO" if relampago else "ACHADO DO DIA",
                   c["alerta"] if relampago else None), VW / 2, 345, 0.1, "pop", 0.4)

    foto = _baixar(p.imagem)
    foto = ajustar(foto, 960, 700)

    def card(d, z):
        d.rounded_rectangle((0, 0, z(1010), z(750)), radius=z(40), fill="#FFFFFF")
    lay_card = camada(1010, 750, card)
    lay_card.paste(foto, ((1010 - foto.width) // 2, (750 - foto.height) // 2), foto.convert("RGBA"))
    r.add(lay_card, VW / 2, 735, 0.2, "pop", 0.5)

    def selo(d, z):
        d.ellipse((z(6), z(6), z(254), z(254)), fill=c["alerta"], outline="#FFFFFF", width=z(8))
        d.text((z(130), z(112)), f"-{p.desconto}%", font=_font(900, 76), fill="#FFFFFF", anchor="mm")
        d.text((z(130), z(178)), "OFF", font=_font(900, 36), fill=c["destaque"], anchor="mm")
    if p.desconto > 0:
        r.add(camada(260, 260, selo).rotate(12, resample=Image.BICUBIC, expand=True), 900, 420, 0.9, "pop", 0.45)

    for i, l in enumerate(_quebrar(ImageDraw.Draw(Image.new("RGB", (1, 1))), p.nome, _font(800, 42),
                                   int((VW - 120) * S), 2)):
        r.add(linha_texto(l, 42, c["texto"], 800), VW / 2, 1150 + i * 50, 1.3 + 0.1 * i, "sobe")

    partes = ([f"Nota {p.nota:.1f}".replace(".", ",")] if p.nota else []) + \
             ([f"{mil(p.vendas)} vendidos"] if p.vendas else []) or [p.plataforma.upper()]
    r.add(linha_texto("  •  ".join(partes), 34, c["suave"], 800), VW / 2, 1258, 1.6, "sobe")
    r.preco = p  # usado no desenho do preço animado
    r.add(botao(cfg, 'COMENTE "QUERO" E RECEBA O LINK'), VW / 2, 1590, 4.4, "pop", 0.5, pulso=True)
    r.add(linha_texto("o link chega no seu direct", 34, c["texto"], 800), VW / 2, 1672, 4.8, "sobe")

    base_quadro = r.quadro

    def quadro(t):
        img = base_quadro(t)
        d = ImageDraw.Draw(img)
        if t >= 2.0 and p.preco_antigo > p.preco:  # preço antigo, riscado em seguida
            antigo = f"De {brl(p.preco_antigo)}"
            fa = _font(800, 22)  # tamanho real 44 (o _font aplica 2x)
            w = d.textlength(antigo, font=fa)
            x0 = VW / 2 - w / 2
            d.text((VW / 2, 1312), antigo, font=fa, fill=c["suave"], anchor="mm")
            pr = ease_out(prog(t, 2.4, 0.4))
            if pr > 0:
                d.line((x0, 1314, x0 + w * pr, 1314), fill=c["alerta"], width=7)
        if t >= 2.6:  # valor "caindo" do antigo até o preço final
            k = ease_out(prog(t, 2.6, 1.2))
            valor = p.preco_antigo + (p.preco - p.preco_antigo) * k if p.preco_antigo > p.preco else p.preco
            fp = _font(900, 60)  # tamanho real 120
            d.text((VW / 2, 1395), brl(valor), font=fp, fill=c["destaque"], anchor="mm")
        if t >= 3.9 and p.preco_antigo - p.preco >= 1:
            k = ease_back(prog(t, 3.9, 0.4))
            txt = f"VOCÊ ECONOMIZA {brl(p.preco_antigo - p.preco)}"
            fe = _font(900, 17)
            w = d.textlength(txt, font=fe) + 50
            h = 64 * max(k, 0.01)
            d.rounded_rectangle((VW / 2 - w / 2, 1475 - h / 2, VW / 2 + w / 2, 1475 + h / 2),
                                radius=int(h / 2), fill=c["ganho"])
            if k > 0.6:
                d.text((VW / 2, 1475), txt, font=fe, fill=c["fundo"], anchor="mm")
        return img

    r.quadro = quadro
    return r


# ---------------- codificação ----------------
def renderizar(roteiro, saida: Path) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    musicas = sorted(AUDIO.glob("*.mp3")) if AUDIO.exists() else []
    dur = roteiro.duracao
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}", "-r", str(FPS), "-i", "-"]
    if musicas:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(musicas))]
        filtro = ["-af", f"afade=t=in:d=0.5,afade=t=out:st={dur - 1:.2f}:d=1,volume=0.7"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000"]
        filtro = []
    cmd += ["-map", "0:v", "-map", "1:a", *filtro,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-profile:v", "high", "-preset", "veryfast",
            "-crf", "20", "-r", str(FPS), "-c:a", "aac", "-b:a", "128k", "-ar", "48000",
            "-t", f"{dur:.2f}", "-movflags", "+faststart", str(saida)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(dur * FPS)):
        proc.stdin.write(roteiro.quadro(i / FPS).tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg falhou ao gerar o vídeo")
    return saida
