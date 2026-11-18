"""Artes de oferta com princípios de neurodesign (1080x1350, formato 4:5).

O que cada elemento faz no cérebro de quem vê:
- Produto grande no centro ........ saliência visual: o olho vai primeiro ao objeto de desejo.
- Selo de % girado e em vermelho .. quebra de padrão + cor de urgência; o número é lido em <0,5 s.
- "De" riscado ao lado do "Por" ... ancoragem: o preço antigo vira referência e o novo parece menor.
- Centavos pequenos ............... efeito do dígito à esquerda: "47" pesa mais que ",90".
- "Você economiza R$ X" ........... aversão à perda: mostrar o que se perde ao não comprar.
- Estrelas + nº de vendidos ....... prova social: reduz o medo de comprar errado.
- Um único botão de alto contraste  efeito Von Restorff: uma ação clara, sem distração.
- Seta apontando para a ação ...... direciona o olhar (pista direcional).
- Leitura em Z .................... marca → produto → preço → botão, nessa ordem.
Tudo é verdadeiro: nada de contador falso ou "últimas unidades" inventado.
"""
import math
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"
W, H = 1080, 1350
K = 2  # desenha em 2x e reduz no fim = bordas suaves (antisserrilhado)


def z(v):
    return int(round(v * K))


def _font(peso: int, tam: float) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / f"Montserrat-{peso}.ttf"), z(tam))


def brl(v: float) -> str:
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mil(n: int) -> str:
    if n >= 1000:
        return f"{n / 1000:.1f}".replace(".", ",").replace(",0", "") + " mil"
    return str(n)


def _quebrar(draw, texto, fonte, largura, max_linhas):
    palavras, linhas, atual = texto.split(), [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if draw.textlength(teste, font=fonte) <= largura:
            atual = teste
            continue
        linhas.append(atual)
        atual = p
        if len(linhas) == max_linhas:
            break
    if len(linhas) < max_linhas and atual:
        linhas.append(atual)
    if " ".join(linhas) != " ".join(palavras):
        while draw.textlength(linhas[-1] + "…", font=fonte) > largura:
            linhas[-1] = linhas[-1][:-1]
        linhas[-1] = linhas[-1].rstrip(" ,-") + "…"
    return linhas


def _fundo(c):
    """Degradê diagonal + brilho radial atrás do produto (puxa o olhar pro centro)."""
    a, b = Image.new("RGB", (z(W), z(H)), c["fundo"]), Image.new("RGB", (z(W), z(H)), c["fundo2"])
    mask = Image.linear_gradient("L").resize((z(W), z(H)))
    img = Image.composite(b, a, mask)
    glow = Image.new("L", (z(W), z(H)), 0)
    ImageDraw.Draw(glow).ellipse((z(140), z(160), z(940), z(860)), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(z(120)))
    return Image.composite(Image.new("RGB", img.size, c["fundo2"]), img, glow)


def _raio(d, x, y, h, cor):
    w = h * 0.6
    pts = [(x + w * .55, y), (x, y + h * .58), (x + w * .45, y + h * .58),
           (x + w * .3, y + h), (x + w, y + h * .38), (x + w * .55, y + h * .38)]
    d.polygon([(z(px), z(py)) for px, py in pts], fill=cor)


def _estrela(d, cx, cy, r, cor):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((z(cx + rr * math.cos(ang)), z(cy + rr * math.sin(ang))))
    d.polygon(pts, fill=cor)


def _sombra(img, caixa, raio, desloc=14, blur=26, alpha=110):
    sh = Image.new("L", img.size, 0)
    x0, y0, x1, y1 = caixa
    ImageDraw.Draw(sh).rounded_rectangle((z(x0), z(y0 + desloc), z(x1), z(y1 + desloc)),
                                         radius=z(raio), fill=alpha)
    sh = sh.filter(ImageFilter.GaussianBlur(z(blur)))
    img.paste(Image.new("RGB", img.size, "#000000"), (0, 0), sh)


UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _baixar(url_ou_img):
    if isinstance(url_ou_img, Image.Image):
        return url_ou_img.convert("RGB")
    candidatos = [url_ou_img]
    if "mlstatic.com" in url_ou_img:  # Mercado Livre: pede a versão grande da foto (-O/-F)
        import re
        for tam in ("F", "O"):
            grande = re.sub(r"-[A-Z]\.(webp|jpg|jpeg|png)$", rf"-{tam}.\1", url_ou_img)
            if grande != url_ou_img:
                candidatos.insert(len(candidatos) - 1, grande)
    erro = None
    for u in candidatos:
        try:
            r = requests.get(u, timeout=30, headers={"User-Agent": UA})
            r.raise_for_status()
            return Image.open(BytesIO(r.content)).convert("RGB")
        except Exception as e:
            erro = e
    raise erro


def ajustar(foto: Image.Image, larg: int, alt: int) -> Image.Image:
    """Redimensiona para caber em larg x alt mantendo a proporção (aumenta ou diminui)."""
    esc = min(larg / foto.width, alt / foto.height)
    return foto.resize((max(1, int(foto.width * esc)), max(1, int(foto.height * esc))), Image.LANCZOS)


def _selo_desconto(img, c, desconto, cx, cy, r=118):
    """Selo circular vermelho, levemente girado (quebra de padrão)."""
    lado = z(r * 2 + 40)
    s = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    m = z(20)
    d.ellipse((m, m, lado - m, lado - m), fill=c["alerta"], outline="#FFFFFF", width=z(7))
    d.text((lado / 2, lado / 2 - z(16)), f"-{desconto}%", font=_font(900, 74), fill="#FFFFFF", anchor="mm")
    d.text((lado / 2, lado / 2 + z(46)), "OFF", font=_font(900, 34), fill=c["destaque"], anchor="mm")
    s = s.rotate(12, resample=Image.BICUBIC)
    img.paste(s, (z(cx) - lado // 2, z(cy) - lado // 2), s)


def _cabecalho(d, c, cfg, etiqueta, cor_etiqueta, cor_txt_etiqueta):
    _raio(d, 52, 40, 58, c["destaque"])
    d.text((z(96), z(69)), cfg["canal"]["nome"], font=_font(900, 40), fill=c["texto"], anchor="lm")
    f = _font(900, 26)
    w = d.textlength(etiqueta, font=f) / K + 52
    d.rounded_rectangle((z(W - 48 - w), z(44), z(W - 48), z(96)), radius=z(26), fill=cor_etiqueta)
    d.text((z(W - 48 - w / 2), z(70)), etiqueta, font=f, fill=cor_txt_etiqueta, anchor="mm")


def _botao(img, d, c, texto, y=1168, h=104):
    caixa = (48, y, W - 48, y + h)
    _sombra(img, caixa, h / 2, desloc=10, blur=18, alpha=140)
    d.rounded_rectangle([z(v) for v in caixa], radius=z(h / 2), fill=c["destaque"])
    tam = 38
    while d.textlength(texto, font=_font(900, tam)) / K > W - 96 - 120 and tam > 24:
        tam -= 1  # encolhe a fonte até caber
    f = _font(900, tam)
    tw = d.textlength(texto, font=f) / K
    seta = 34
    x0 = W / 2 - (tw + 20 + seta) / 2
    d.text((z(x0), z(y + h / 2)), texto, font=f, fill=c["fundo"], anchor="lm")
    ax, ay = x0 + tw + 20, y + h / 2  # seta pra baixo/direita
    d.polygon([(z(ax), z(ay - 14)), (z(ax + seta), z(ay - 14)), (z(ax + seta / 2), z(ay + 16))], fill=c["fundo"])


def _rodape(d, c, texto, y=1302):
    d.text((z(W / 2), z(y)), texto, font=_font(800, 22), fill=c["suave"], anchor="mm")


def arte_produto(cfg, p, canal: str = "telegram") -> Image.Image:
    """Layout com a FOTO como protagonista: faixa fina da marca, área branca grande com o
    produto e, embaixo, a faixa de informações (nome, preço, economia, botão)."""
    c = cfg["cores"]
    img = _fundo(c)
    d = ImageDraw.Draw(img)

    relampago = p.desconto >= 50
    # Faixa da marca (fina)
    _raio(d, 40, 22, 52, c["destaque"])
    d.text((z(80), z(48)), cfg["canal"]["nome"], font=_font(900, 36), fill=c["texto"], anchor="lm")
    etiqueta = "OFERTA RELÂMPAGO" if relampago else "ACHADO DO DIA"
    f = _font(900, 24)
    w = d.textlength(etiqueta, font=f) / K + 44
    d.rounded_rectangle((z(W - 36 - w), z(24), z(W - 36), z(72)), radius=z(24),
                        fill=c["alerta"] if relampago else c["destaque"])
    d.text((z(W - 36 - w / 2), z(48)), etiqueta, font=f, fill="#FFFFFF" if relampago else c["fundo"], anchor="mm")

    # Cartão branco grande com o produto (fundo roxo em volta)
    area = (28, 100, W - 28, 836)
    _sombra(img, area, 40, desloc=10, blur=20, alpha=120)
    d.rounded_rectangle([z(v) for v in area], radius=z(40), fill="#FFFFFF")
    foto = ajustar(_baixar(p.imagem), z(area[2] - area[0] - 50), z(area[3] - area[1] - 50))
    img.paste(foto, (z(W / 2) - foto.width // 2, z((area[1] + area[3]) / 2) - foto.height // 2))

    if p.desconto > 0:
        _selo_desconto(img, c, p.desconto, W - 140, 240, r=104)

    # Prova social sobre a foto (só o que existir de verdade)
    partes = ([f"{p.nota:.1f}".replace(".", ",")] if p.nota else []) + \
             ([f"{mil(p.vendas)} vendidos"] if p.vendas else [])
    if partes:
        txt = "  •  ".join(partes)
        f = _font(800, 28)
        estrelas = 5 * 30 + 16 if p.nota else 0
        pw = estrelas + d.textlength(txt, font=f) / K + 48
        py = area[3] - 76
        d.rounded_rectangle((z(48), z(py), z(48 + pw), z(py + 56)), radius=z(28), fill="#F4F0FA")
        if p.nota:
            for i in range(5):
                _estrela(d, 80 + i * 30, py + 28, 13, "#FFB800")
        d.text((z(72 + estrelas), z(py + 28)), txt, font=f, fill="#2B2340", anchor="lm")

    # Nome (até 2 linhas)
    y = 858
    for linha in _quebrar(d, p.nome, _font(800, 34), z(W - 80), 2):
        d.text((z(40), z(y)), linha, font=_font(800, 34), fill=c["texto"])
        y += 42

    # Preço: âncora → preço → ganho
    if p.preco_antigo > p.preco:
        ft = _font(700, 30) if (FONTS / "Montserrat-700.ttf").exists() else _font(800, 30)
        antigo = f"De {brl(p.preco_antigo)}"
        ya = 950
        d.text((z(40), z(ya)), antigo, font=ft, fill=c["suave"])
        x_ini = 40 + d.textlength("De ", font=ft) / K
        x_fim = 40 + d.textlength(antigo, font=ft) / K
        d.line((z(x_ini), z(ya + 19), z(x_fim), z(ya + 19)), fill=c["alerta"], width=z(5))
    reais, cent = f"{p.preco:,.2f}".replace(",", ".").rsplit(".", 1)
    x, base = 40, 1118
    d.text((z(x), z(base - 84)), "POR", font=_font(900, 24), fill=c["destaque"], anchor="ls")
    d.text((z(x), z(base - 50)), "R$", font=_font(900, 36), fill=c["destaque"], anchor="ls")
    x += 64
    fr = _font(900, 128)
    d.text((z(x), z(base)), reais, font=fr, fill=c["destaque"], anchor="ls")
    x += d.textlength(reais, font=fr) / K + 6
    d.text((z(x), z(base - 58)), f",{cent}", font=_font(900, 48), fill=c["destaque"], anchor="ls")

    economia = p.preco_antigo - p.preco
    if economia >= 1:
        bx0, by0, bx1, by1 = 690, 1000, W - 36, 1112
        d.rounded_rectangle((z(bx0), z(by0), z(bx1), z(by1)), radius=z(26), fill=c["ganho"])
        d.text((z((bx0 + bx1) / 2), z(by0 + 34)), "VOCÊ ECONOMIZA", font=_font(900, 22),
               fill=c["fundo"], anchor="mm")
        d.text((z((bx0 + bx1) / 2), z(by0 + 78)), brl(economia), font=_font(900, 42),
               fill=c["fundo"], anchor="mm")

    cta = "COMPRE NO BOTÃO ABAIXO" if canal == "telegram" else 'COMENTE "QUERO" E RECEBA O LINK'
    _botao(img, d, c, cta, y=1150, h=96)
    _rodape(d, c, "PREÇO SUJEITO A ALTERAÇÃO A QUALQUER MOMENTO"
            if canal == "telegram" else "O LINK CHEGA NO SEU DIRECT EM SEGUNDOS", y=1290)
    return img.resize((W, H), Image.LANCZOS)


def arte_campanha(cfg, nome, imagem, horas_restantes=None) -> Image.Image:
    c = cfg["cores"]
    img = _fundo(c)
    d = ImageDraw.Draw(img)
    _cabecalho(d, c, cfg, "CUPONS LIBERADOS", c["alerta"], "#FFFFFF")

    card = (48, 124, W - 48, 700)
    _sombra(img, card, 44)
    d.rounded_rectangle([z(v) for v in card], radius=z(44), fill="#FFFFFF")
    foto = _baixar(imagem)
    foto.thumbnail((z(card[2] - card[0] - 80), z(card[3] - card[1] - 80)), Image.LANCZOS)
    img.paste(foto, (z((card[0] + card[2]) / 2) - foto.width // 2,
                     z((card[1] + card[3]) / 2) - foto.height // 2))

    y = 730
    for linha in _quebrar(d, nome, _font(800, 40), z(W - 96), 2):
        d.text((z(48), z(y)), linha, font=_font(800, 40), fill=c["texto"])
        y += 50
    d.text((z(48), z(880)), "CUPONS E", font=_font(900, 84), fill=c["destaque"])
    d.text((z(48), z(975)), "DESCONTOS", font=_font(900, 84), fill=c["destaque"])

    # Escassez real: só mostra o prazo se a Shopee informar o fim da campanha
    if horas_restantes is not None and horas_restantes <= 48:
        txt = f"TERMINA EM {max(1, int(horas_restantes))}H"
        d.rounded_rectangle((z(48), z(1092), z(48 + 40 + d.textlength(txt, font=_font(900, 32)) / K),
                             z(1148)), radius=z(28), fill=c["alerta"])
        d.text((z(68), z(1120)), txt, font=_font(900, 32), fill="#FFFFFF", anchor="lm")
    else:
        d.text((z(48), z(1092)), "POR TEMPO LIMITADO", font=_font(900, 32), fill=c["texto"])

    _botao(img, d, c, "PEGUE SEU CUPOM AGORA")
    _rodape(d, c, "CUPONS LIMITADOS • PODEM ESGOTAR ANTES DO PRAZO")
    return img.resize((W, H), Image.LANCZOS)


def salvar(img: Image.Image, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    img.save(caminho, "JPEG", quality=92, optimize=True)
    return caminho
