"""Gera os 6 posts de lançamento do Instagram, a foto de perfil e o ícone do app.

Uso: python -m bot.posts_iniciais   → arquivos em posts_iniciais/
"""
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from .art import H, K, W, _botao, _estrela, _fundo, _font, _quebrar, _raio, _sombra, salvar, z

RAIZ = Path(__file__).resolve().parent.parent
OUT = RAIZ / "posts_iniciais"


def _base(cfg, etiqueta, num):
    c = cfg["cores"]
    img = _fundo(c)
    d = ImageDraw.Draw(img)
    _raio(d, 52, 40, 58, c["destaque"])
    d.text((z(96), z(69)), cfg["canal"]["nome"], font=_font(900, 40), fill=c["texto"], anchor="lm")
    f = _font(900, 26)
    w = d.textlength(etiqueta, font=f) / K + 52
    d.rounded_rectangle((z(W - 48 - w), z(44), z(W - 48), z(96)), radius=z(26), fill=c["alerta"])
    d.text((z(W - 48 - w / 2), z(70)), etiqueta, font=f, fill="#FFFFFF", anchor="mm")
    d.text((z(W - 48), z(H - 40)), f"{num}/6", font=_font(800, 24), fill=c["suave"], anchor="rm")
    return img, d, c


def _titulo(d, c, linhas, y, tam=96, cores=None):
    for i, linha in enumerate(linhas):
        cor = (cores or [c["texto"]] * len(linhas))[i]
        d.text((z(48), z(y)), linha, font=_font(900, tam), fill=cor)
        y += tam * 1.08
    return y


def _paragrafo(d, c, texto, y, tam=36, cor=None, largura=W - 96):
    for linha in _quebrar(d, texto, _font(800, tam), z(largura), 6):
        d.text((z(48), z(y)), linha, font=_font(800, tam), fill=cor or c["suave"])
        y += tam * 1.4
    return y


def _item(img, d, c, y, numero, titulo, sub, cor_num=None):
    _sombra(img, (48, y, W - 48, y + 150), 32, desloc=8, blur=16, alpha=90)
    d.rounded_rectangle((z(48), z(y), z(W - 48), z(y + 150)), radius=z(32), fill="#FFFFFF")
    d.ellipse((z(78), z(y + 30), z(168), z(y + 120)), fill=cor_num or c["alerta"])
    if numero == "★":
        _estrela(d, 123, y + 77, 28, "#FFFFFF")
    elif numero == "✓":
        d.line([(z(103), z(y + 76)), (z(118), z(y + 92)), (z(145), z(y + 60))], fill="#FFFFFF", width=z(9))
    else:
        d.text((z(123), z(y + 75)), numero, font=_font(900, 44), fill="#FFFFFF", anchor="mm")
    d.text((z(196), z(y + 52)), titulo, font=_font(900, 36), fill=c["fundo"], anchor="lm")
    d.text((z(196), z(y + 102)), sub, font=_font(800, 26), fill="#5B5470", anchor="lm")


def post1(cfg):  # Apresentação
    img, d, c = _base(cfg, "CHEGAMOS!", 1)
    y = _titulo(d, c, ["OFERTAS", "DE VERDADE.", "TODO DIA."], 240, 118,
                [c["texto"], c["destaque"], c["destaque"]])
    y = _paragrafo(d, c, "A gente garimpa as melhores promoções e cupons da internet e entrega pra você "
                         "antes de todo mundo. Você só aproveita.", y + 40, 40)
    # selo grande
    cx, cy, r = W / 2, 990, 140
    d.ellipse((z(cx - r), z(cy - r), z(cx + r), z(cy + r)), fill=c["alerta"])
    d.text((z(cx), z(cy - 40)), "ATÉ", font=_font(900, 40), fill="#FFFFFF", anchor="mm")
    d.text((z(cx), z(cy + 20)), "-70%", font=_font(900, 92), fill="#FFFFFF", anchor="mm")
    d.text((z(cx), z(cy + 82)), "OFF", font=_font(900, 36), fill=c["destaque"], anchor="mm")
    _botao(img, d, c, "SIGA E ATIVE AS NOTIFICAÇÕES")
    return img


def post2(cfg):  # Como funciona
    img, d, c = _base(cfg, "COMO FUNCIONA", 2)
    _titulo(d, c, ["RECEBA O LINK", "EM 3 PASSOS"], 180, 88, [c["texto"], c["destaque"]])
    _item(img, d, c, 430, "1", "Viu uma oferta?", "Todo dia tem achado novo no feed")
    _item(img, d, c, 610, "2", 'Comente "QUERO"', "Na publicação do produto")
    _item(img, d, c, 790, "3", "Receba no direct", "O link chega em segundos", c["ganho"])
    _paragrafo(d, c, "Simples assim. Sem cadastro, sem custo, sem pegadinha.", 980, 36)
    _botao(img, d, c, "TESTE NA PRÓXIMA OFERTA")
    return img


def post3(cfg):  # Telegram
    img, d, c = _base(cfg, "TELEGRAM", 3)
    y = _titulo(d, c, ["OFERTA", "RELÂMPAGO", "ACABA RÁPIDO."], 200, 112,
                [c["texto"], c["destaque"], c["texto"]])
    y = _paragrafo(d, c, "No nosso canal do Telegram as ofertas saem na hora, 24 horas por dia, "
                         "com o link direto pra comprar. Quem chega primeiro, paga menos.", y + 40, 40)
    tg = cfg["canal"]["arroba_telegram"]
    _sombra(img, (48, 930, W - 48, 1080), 36)
    d.rounded_rectangle((z(48), z(930), z(W - 48), z(1080)), radius=z(36), fill="#FFFFFF")
    d.text((z(W / 2), z(985)), "PROCURE NO TELEGRAM", font=_font(900, 28), fill="#5B5470", anchor="mm")
    d.text((z(W / 2), z(1035)), tg, font=_font(900, 54), fill=c["fundo2"], anchor="mm")
    _botao(img, d, c, "LINK NA BIO")
    return img


def post4(cfg):  # Filtro / confiança
    f = cfg["filtros"]
    img, d, c = _base(cfg, "NOSSO FILTRO", 4)
    _titulo(d, c, ["NÃO É QUALQUER", "OFERTA QUE", "ENTRA AQUI."], 170, 86,
            [c["texto"], c["texto"], c["destaque"]])
    _item(img, d, c, 500, "%", f"Desconto mínimo de {f['desconto_minimo']}%", "Promoção de verdade, não de mentirinha")
    _item(img, d, c, 680, "★", f"Nota {str(f['nota_minima']).replace('.', ',')} ou mais",
          "Produto bem avaliado por quem comprou", "#FFB800")
    _item(img, d, c, 860, "✓", f"Mais de {f['vendas_minimas']} vendidos", "Vendedor com histórico", c["ganho"])
    _paragrafo(d, c, "Comparamos preço, avaliação e vendas antes de publicar.", 1050, 34)
    _botao(img, d, c, "SALVE PRA NÃO PERDER")
    return img


def post5(cfg):  # Dicas
    img, d, c = _base(cfg, "SALVE ESTE POST", 5)
    _titulo(d, c, ["5 DICAS PRA", "PAGAR MENOS"], 160, 92, [c["texto"], c["destaque"]])
    dicas = [
        ("Junte cupons", "Cupom da loja + cupom de frete na mesma compra"),
        ("Use as moedas", "Moedas Shopee viram desconto no checkout"),
        ("Datas duplas", "9.9, 10.10, 11.11 e 12.12 têm os maiores cupons"),
        ("Leia as avaliações", "Prefira as que têm foto de quem comprou"),
        ("Compare o vendedor", "O mesmo produto pode ter preços diferentes"),
    ]
    y = 390
    for i, (t, s) in enumerate(dicas, 1):
        d.ellipse((z(48), z(y), z(118), z(y + 70)), fill=c["alerta"] if i % 2 else c["destaque"])
        d.text((z(83), z(y + 35)), str(i), font=_font(900, 38),
               fill="#FFFFFF" if i % 2 else c["fundo"], anchor="mm")
        d.text((z(144), z(y + 18)), t, font=_font(900, 38), fill=c["texto"], anchor="lm")
        d.text((z(144), z(y + 60)), s, font=_font(800, 26), fill=c["suave"], anchor="lm")
        y += 145
    _botao(img, d, c, "MANDE PRA QUEM AMA DESCONTO")
    return img


def post6(cfg):  # Transparência
    img, d, c = _base(cfg, "TRANSPARÊNCIA", 6)
    y = _titulo(d, c, ["VOCÊ PAGA", "O MESMO", "PREÇO."], 200, 118,
                [c["texto"], c["texto"], c["destaque"]])
    y = _paragrafo(d, c, "Nossos links são de afiliado: quando você compra por eles, a loja nos paga uma "
                         "pequena comissão. Pra você, o preço é exatamente o mesmo.", y + 40, 40)
    _paragrafo(d, c, "É assim que mantemos o canal no ar, de graça, garimpando ofertas todos os dias. "
                     "Obrigado por apoiar!", y + 30, 40, c["texto"])
    _botao(img, d, c, "COMPRE PELOS NOSSOS LINKS")
    return img


LEGENDAS = [
    """⚡ Chegou o comdescontaco!

Todo dia a gente garimpa as melhores promoções, cupons e ofertas relâmpago da internet, e entrega pra você antes de todo mundo.

✅ Descontos de até 70%
✅ Só produtos bem avaliados
✅ Link direto, sem enrolação

👉 Siga @comdescontaco e ative as notificações pra não perder nenhuma oferta.

#promoção #achadinhos #ofertas #desconto #cupom #shopee #economia #comdescontaco""",
    """📩 Receber o link de uma oferta é muito fácil:

1️⃣ Viu uma oferta no nosso feed?
2️⃣ Comente QUERO na publicação
3️⃣ O link chega no seu direct em segundos

Sem cadastro, sem custo, sem pegadinha. 😉

Comenta QUERO aqui embaixo se você ama um desconto! 👇

#achadinhos #promoção #ofertas #desconto #comdescontaco""",
    """⚡ Oferta relâmpago acaba rápido!

No nosso canal do Telegram as ofertas saem na hora, 24 horas por dia, com o link direto pra comprar.

📲 Procure @comdescontaco no Telegram ou toque no link da bio.

Quem chega primeiro, paga menos. 🏃‍♀️💨

#telegram #promoção #ofertasrelampago #achadinhos #comdescontaco""",
    """🔎 Não é qualquer oferta que entra aqui.

Antes de publicar, cada produto passa pelo nosso filtro:
✅ Desconto mínimo de 30%
⭐ Nota 4,6 ou mais
📦 Mais de 100 vendidos

Promoção de verdade, de vendedor com histórico. Salve este post! 📌

#achadinhos #comprasonline #promoção #dicas #comdescontaco""",
    """💸 5 dicas pra pagar menos nas compras on-line:

1. Junte cupom da loja + cupom de frete
2. Use as moedas Shopee no checkout
3. Aproveite as datas duplas (9.9, 10.10, 11.11, 12.12)
4. Leia as avaliações com foto
5. Compare vendedores do mesmo produto

Salve 📌 e mande pra quem ama um desconto! 👇

#dicas #economia #cupom #shopee #promoção #comdescontaco""",
    """🤝 Transparência total com você:

Nossos links são de afiliado. Quando você compra por eles, a loja nos paga uma pequena comissão, e você paga EXATAMENTE o mesmo preço.

É assim que mantemos o canal no ar, de graça, garimpando ofertas todos os dias.

Obrigado por apoiar! 💜

#publi #linkdeafiliado #transparencia #comdescontaco""",
]


def foto_perfil(cfg, lado=1080):
    c = cfg["cores"]
    img = Image.new("RGB", (lado * K // 1, lado * K // 1), c["fundo"])
    a = Image.new("RGB", img.size, c["fundo2"])
    mask = Image.radial_gradient("L").resize(img.size)
    img = Image.composite(img, a, mask)
    d = ImageDraw.Draw(img)
    s = lado / 1080
    h = 600 * s  # raio centralizado (a foto de perfil é cortada em círculo)
    _raio(d, lado / 2 - h * 0.35, lado / 2 - h / 2, h, c["destaque"])
    return img.resize((lado, lado), Image.LANCZOS)


def main():
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text())
    OUT.mkdir(exist_ok=True)
    for i, fn in enumerate([post1, post2, post3, post4, post5, post6], 1):
        salvar(fn(cfg).resize((W, H), Image.LANCZOS), OUT / f"post_{i}.jpg")
    (OUT / "legendas.txt").write_text(
        "\n\n".join(f"===== POST {i} =====\n{t}" for i, t in enumerate(LEGENDAS, 1)))
    salvar(foto_perfil(cfg), OUT / "foto_perfil.jpg")
    foto_perfil(cfg, 1024).save(OUT / "icone_app_1024.png")
    print(f"Arquivos em {OUT}")


if __name__ == "__main__":
    main()
