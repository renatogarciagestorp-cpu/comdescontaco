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


def _baixar(url_ou_img):
    if isinstance(url_ou_img, Image.Image):
        return url_ou_img.convert("RGB")
    r = requests.get(url_ou_img, timeout=30)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGB")


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
    """p: objeto com nome, imagem, preco, preco_antigo, desconto, nota, vendas."""
    c = cfg["cores"]
    img = _fundo(c)
    d = ImageDraw.Draw(img)

    relampago = p.desconto >= 50
    _cabecalho(d, c, cfg, "OFERTA RELÂMPAGO" if relampago else "ACHADO DO DIA",
               c["alerta"] if relampago else c["destaque"], "#FFFFFF" if relampago else c["fundo"])

    # Cartão do produto (herói)
    card = (48, 124, W - 48, 772)
    _sombra(img, card, 44)
    d.rounded_rectangle([z(v) for v in card], radius=z(44), fill="#FFFFFF")
    foto = _baixar(p.imagem)
    foto.thumbnail((z(card[2] - card[0] - 120), z(card[3] - card[1] - 130)), Image.LANCZOS)
    img.paste(foto, (z((card[0] + card[2]) / 2) - foto.width // 2, z(card[1] + 30)))

    # Prova social dentro do cartão
    txt = f"{p.nota:.1f}".replace(".", ",") + f"  •  {mil(p.vendas)} vendidos"
    f = _font(800, 28)
    pw = 5 * 30 + 16 + d.textlength(txt, font=f) / K + 48
    py = card[3] - 82
    d.rounded_rectangle((z(card[0] + 24), z(py), z(card[0] + 24 + pw), z(py + 58)),
                        radius=z(29), fill="#F4F0FA")
    for i in range(5):
        _estrela(d, card[0] + 56 + i * 30, py + 29, 13, "#FFB800")
    d.text((z(card[0] + 56 + 5 * 30), z(py + 29)), txt, font=f, fill="#2B2340", anchor="lm")

    _selo_desconto(img, c, p.desconto, W - 168, 248)

    # Título curto (menos carga cognitiva)
    y = 800
    for linha in _quebrar(d, p.nome, _font(800, 38), z(W - 96), 2):
        d.text((z(48), z(y)), linha, font=_font(800, 38), fill=c["texto"])
        y += 48

    # Bloco de preço: âncora → preço → ganho
    y = 912
    if p.preco_antigo > p.preco:
        ft = _font(700, 34) if (FONTS / "Montserrat-700.ttf").exists() else _font(800, 34)
        antigo = f"De {brl(p.preco_antigo)}"
        d.text((z(48), z(y)), antigo, font=ft, fill=c["suave"])
        x_ini = 48 + d.textlength("De ", font=ft) / K
        x_fim = 48 + d.textlength(antigo, font=ft) / K
        d.line((z(x_ini), z(y + 21), z(x_fim), z(y + 21)), fill=c["alerta"], width=z(5))
    reais, cent = f"{p.preco:,.2f}".replace(",", ".").rsplit(".", 1)
    x, base = 48, 1100
    d.text((z(x), z(base - 96)), "POR", font=_font(900, 26), fill=c["destaque"], anchor="ls")
    d.text((z(x), z(base - 58)), "R$", font=_font(900, 40), fill=c["destaque"], anchor="ls")
    x += 72
    fr = _font(900, 150)
    d.text((z(x), z(base)), reais, font=fr, fill=c["destaque"], anchor="ls")
    x += d.textlength(reais, font=fr) / K + 6
    d.text((z(x), z(base - 66)), f",{cent}", font=_font(900, 56), fill=c["destaque"], anchor="ls")

    # Aversão à perda: quanto a pessoa economiza
    economia = p.preco_antigo - p.preco
    if economia >= 1:
        bx0, by0, bx1, by1 = 662, 966, W - 48, 1094
        d.rounded_rectangle((z(bx0), z(by0), z(bx1), z(by1)), radius=z(28), fill=c["ganho"])
        d.text((z((bx0 + bx1) / 2), z(by0 + 38)), "VOCÊ ECONOMIZA", font=_font(900, 24),
               fill=c["fundo"], anchor="mm")
        d.text((z((bx0 + bx1) / 2), z(by0 + 88)), brl(economia), font=_font(900, 46),
               fill=c["fundo"], anchor="mm")

    cta = "COMPRE NO BOTÃO ABAIXO" if canal == "telegram" else 'COMENTE "QUERO" E RECEBA O LINK'
    _botao(img, d, c, cta)
    _rodape(d, c, "PREÇO SUJEITO A ALTERAÇÃO A QUALQUER MOMENTO"
            if canal == "telegram" else "O LINK CHEGA NO SEU DIRECT EM SEGUNDOS")
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
