"""Gera a arte 1080x1080 de cada oferta (serve para Telegram e Instagram)."""
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
S = 1080


def _font(peso: int, tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / f"Montserrat-{peso}.ttf"), tam)


def _brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _quebrar(draw, texto, fonte, largura, max_linhas):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if draw.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
            if len(linhas) == max_linhas:
                break
    if len(linhas) < max_linhas and atual:
        linhas.append(atual)
    if len(linhas) == max_linhas and " ".join(linhas) != texto:
        while draw.textlength(linhas[-1] + "…", font=fonte) > largura:
            linhas[-1] = linhas[-1][:-1]
        linhas[-1] = linhas[-1].rstrip() + "…"
    return linhas


def _degrade(c1, c2):
    top, bot = Image.new("RGB", (S, S), c1), Image.new("RGB", (S, S), c2)
    mask = Image.linear_gradient("L").resize((S, S))
    return Image.composite(bot, top, mask)


def _raio(draw, x, y, h, cor):
    """Pequeno raio (ícone) desenhado em polígono."""
    w = h * 0.6
    pts = [(x + w * 0.55, y), (x, y + h * 0.58), (x + w * 0.45, y + h * 0.58),
           (x + w * 0.3, y + h), (x + w, y + h * 0.38), (x + w * 0.55, y + h * 0.38)]
    draw.polygon(pts, fill=cor)


def _baixar_imagem(url_ou_img):
    if isinstance(url_ou_img, Image.Image):
        return url_ou_img.convert("RGB")
    r = requests.get(url_ou_img, timeout=30)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


def gerar_arte(cfg: dict, titulo: str, imagem, preco: float | None = None,
               preco_antigo: float | None = None, desconto: int | None = None,
               selo: str = "OFERTA", rodape: str = "LINK NO TELEGRAM") -> Image.Image:
    c = cfg["cores"]
    img = _degrade(c["fundo"], c["fundo2"])
    d = ImageDraw.Draw(img)

    # Cabeçalho: marca
    _raio(d, 60, 44, 64, c["destaque"])
    d.text((112, 52), cfg["canal"]["nome"].upper(), font=_font(900, 44), fill=c["texto"])
    sw = d.textlength(selo, font=_font(800, 30)) + 48
    d.rounded_rectangle((S - 60 - sw, 50, S - 60, 104), radius=27, fill=c["destaque"])
    d.text((S - 60 - sw / 2, 77), selo, font=_font(800, 30), fill=c["fundo"], anchor="mm")

    # Cartão branco com a foto do produto
    card = (60, 140, S - 60, 700)
    d.rounded_rectangle(card, radius=36, fill="#FFFFFF")
    foto = _baixar_imagem(imagem)
    foto.thumbnail((card[2] - card[0] - 80, card[3] - card[1] - 60))
    fx = card[0] + (card[2] - card[0] - foto.width) // 2
    fy = card[1] + (card[3] - card[1] - foto.height) // 2
    img.paste(foto, (fx, fy))

    # Selo de desconto
    if desconto:
        cx, cy, r = S - 175, 255, 100
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c["alerta"])
        d.text((cx, cy - 12), f"-{desconto}%", font=_font(900, 58), fill="#FFFFFF", anchor="mm")
        d.text((cx, cy + 40), "OFF", font=_font(800, 30), fill="#FFFFFF", anchor="mm")

    # Título
    y = 730
    for linha in _quebrar(d, titulo, _font(800, 38), S - 120, 2):
        d.text((60, y), linha, font=_font(800, 38), fill=c["texto"])
        y += 48

    # Preços
    y = 845
    if preco is not None:
        if preco_antigo and preco_antigo > preco:
            antigo = f"de {_brl(preco_antigo)}"
            f = _font(600, 34)
            d.text((60, y), antigo, font=f, fill="#CBB8F0")
            w = d.textlength(antigo, font=f)
            d.line((60 + d.textlength('de ', font=f), y + 22, 60 + w, y + 22), fill="#CBB8F0", width=4)
        d.text((60, y + 42), _brl(preco), font=_font(900, 92), fill=c["destaque"])
    else:
        d.text((60, y + 20), "CUPONS E OFERTAS", font=_font(900, 64), fill=c["destaque"])
        d.text((60, y + 95), "LIBERADOS AGORA", font=_font(900, 40), fill=c["texto"])

    # Rodapé (CTA)
    f = _font(800, 30)
    w = d.textlength(rodape, font=f) + 60
    d.rounded_rectangle((S - 60 - w, 960, S - 60, 1024), radius=32, fill=c["alerta"])
    d.text((S - 60 - w / 2, 992), rodape, font=f, fill="#FFFFFF", anchor="mm")
    return img


def salvar(img: Image.Image, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(caminho, "JPEG", quality=90)
    return caminho
