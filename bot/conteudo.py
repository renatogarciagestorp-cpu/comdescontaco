"""Publica 1 post de conteúdo por dia no Instagram (feed + Stories), a partir de conteudo/banco.yaml.

Uso:
  python -m bot.conteudo --gerar     # gera a arte do próximo post em arts/ e marca na fila
  python -m bot.conteudo --publicar  # publica no Instagram o que foi gerado (depois do git push)
  python -m bot.conteudo --previa    # gera todas as artes em preview/conteudo/ (sem publicar)
  python -m bot.conteudo --destaques # gera as capas dos destaques em preview/destaques/
"""
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from PIL import Image, ImageDraw

from .art import H, K, W, _botao, _fundo, _font, _raio, salvar, z
from .posts_iniciais import _item, _paragrafo, _titulo

RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "conteudo" / "banco.yaml"
ESTADO = RAIZ / "data" / "conteudo_state.json"
ARTS = RAIZ / "arts"
BR = ZoneInfo("America/Sao_Paulo")


def _cabecalho(img, cfg, etiqueta):
    c = cfg["cores"]
    d = ImageDraw.Draw(img)
    _raio(d, 52, 40, 58, c["destaque"])
    d.text((z(96), z(69)), cfg["canal"]["nome"], font=_font(900, 40), fill=c["texto"], anchor="lm")
    f = _font(900, 26)
    w = d.textlength(etiqueta, font=f) / K + 52
    d.rounded_rectangle((z(W - 48 - w), z(44), z(W - 48), z(96)), radius=z(26), fill=c["alerta"])
    d.text((z(W - 48 - w / 2), z(70)), etiqueta, font=f, fill="#FFFFFF", anchor="mm")
    return d, c


def _tam_titulo(d, linhas, maximo):
    """Maior tamanho de fonte (até 'maximo') em que todas as linhas cabem na largura."""
    tam = maximo
    while tam > 40 and max(d.textlength(l, font=_font(900, tam)) for l in linhas) / K > W - 96:
        tam -= 2
    return tam


def _cores_titulo(c, post):
    return [c["destaque"] if i in post.get("destaque", []) else c["texto"]
            for i in range(len(post["titulo"]))]


def arte(cfg, post, hoje: date) -> Image.Image | None:
    img = _fundo(cfg["cores"])
    d, c = _cabecalho(img, cfg, post["etiqueta"])
    tipo = post["tipo"]

    if tipo == "lista":
        y = _titulo(d, c, post["titulo"], 170, _tam_titulo(d, post["titulo"], 84), _cores_titulo(c, post))
        n = len(post["itens"])
        passo = 150 if n <= 4 else 140
        alto = 130 if n <= 4 else 122
        y = max(y + 30, 400)
        for i, (t, s) in enumerate(post["itens"], 1):
            _item_compacto(img, d, c, y, str(i), t, s, alto)
            y += passo
    elif tipo == "texto":
        y = _titulo(d, c, post["titulo"], 220, _tam_titulo(d, post["titulo"], 104), _cores_titulo(c, post))
        _paragrafo(d, c, post["texto"], y + 50, 40)
    elif tipo == "contagem":
        alvo = date.fromisoformat(post["data_alvo"])
        dias = (alvo - hoje).days
        if dias < 1:
            return None  # data já passou: pula este post
        d.text((z(W / 2), z(230)), "FALTAM", font=_font(900, 60), fill=c["texto"], anchor="mm")
        d.text((z(W / 2), z(470)), str(dias), font=_font(900, 380), fill=c["destaque"], anchor="mm")
        d.text((z(W / 2), z(700)), "DIA" if dias == 1 else "DIAS", font=_font(900, 80),
               fill=c["texto"], anchor="mm")
        d.text((z(W / 2), z(800)), f"PARA A {post['evento']}", font=_font(900, 54),
               fill=c["alerta"], anchor="mm")
        _paragrafo(d, c, post["texto"], 900, 38)
    else:
        raise ValueError(f"tipo desconhecido: {tipo}")

    _botao(img, d, c, post["cta"])
    return img.resize((W, H), Image.LANCZOS)


def _item_compacto(img, d, c, y, numero, titulo, sub, alto):
    """Igual ao _item dos posts iniciais, com altura ajustável para listas de 5 itens."""
    if alto >= 150:
        return _item(img, d, c, y, numero, titulo, sub)
    d.rounded_rectangle((z(48), z(y), z(W - 48), z(y + alto)), radius=z(30), fill="#FFFFFF")
    m = y + alto / 2
    d.ellipse((z(74), z(m - 40), z(154), z(m + 40)), fill=c["alerta"])
    d.text((z(114), z(m)), numero, font=_font(900, 40), fill="#FFFFFF", anchor="mm")
    d.text((z(180), z(m - 22)), titulo, font=_font(900, 34), fill=c["fundo"], anchor="lm")
    d.text((z(180), z(m + 24)), sub, font=_font(800, 24), fill="#5B5470", anchor="lm")


def story(cfg, feed: Image.Image) -> Image.Image:
    """Versão 1080x1920 para Stories: o post no centro + chamada para o perfil."""
    c = cfg["cores"]
    SW, SH = 1080, 1920
    a = Image.new("RGB", (SW, SH), c["fundo"])
    b = Image.new("RGB", (SW, SH), c["fundo2"])
    img = Image.composite(b, a, Image.linear_gradient("L").resize((SW, SH)))
    d = ImageDraw.Draw(img)
    d.text((SW / 2, 190), "NOVO POST", font=ImageFont_(900, 64), fill=c["destaque"], anchor="mm")
    f = feed.resize((900, 1125), Image.LANCZOS)
    img.paste(f, ((SW - 900) // 2, 290))
    d.rounded_rectangle((170, 1500, SW - 170, 1600), radius=50, fill=c["destaque"])
    d.text((SW / 2, 1550), "VEJA NO NOSSO PERFIL", font=ImageFont_(900, 40), fill=c["fundo"], anchor="mm")
    d.text((SW / 2, 1680), cfg["canal"]["arroba_instagram"], font=ImageFont_(800, 44), fill=c["texto"], anchor="mm")
    return img


def ImageFont_(peso, tam):  # fonte em tamanho real (sem o fator K)
    return _font(peso, tam / K)


def carregar():
    banco = yaml.safe_load(BANCO.read_text())["posts"]
    estado = json.loads(ESTADO.read_text()) if ESTADO.exists() else {"publicados": [], "fila": None}
    return banco, estado


def gerar(cfg):
    banco, estado = carregar()
    hoje = datetime.now(BR).date()
    # Posts com "publicar_em" saem exatamente nesse dia; os demais seguem a ordem do banco.
    do_dia = [p for p in banco if p.get("publicar_em") == hoje.isoformat()]
    normais = [p for p in banco if not p.get("publicar_em")]
    for post in do_dia + normais:
        if post["id"] in estado["publicados"]:
            continue
        img = arte(cfg, post, hoje)
        if img is None:  # contagem com data vencida
            estado["publicados"].append(post["id"])
            continue
        nome = f"conteudo_{post['id']}_{hoje:%Y%m%d}"
        salvar(img, ARTS / f"{nome}.jpg")
        salvar(story(cfg, img), ARTS / f"{nome}_story.jpg")
        video = None
        if cfg.get("instagram", {}).get("conteudo_em_reels", True):
            try:
                from .video import renderizar, roteiro_conteudo
                dias = (date.fromisoformat(post["data_alvo"]) - hoje).days if post["tipo"] == "contagem" else None
                renderizar(roteiro_conteudo(cfg, post, dias), ARTS / f"{nome}.mp4")
                video = f"{nome}.mp4"
            except Exception as e:
                print(f"[aviso] vídeo não gerado, vai como imagem: {e}")
        estado["fila"] = {"id": post["id"], "arquivo": f"{nome}.jpg", "story": f"{nome}_story.jpg",
                          "video": video, "legenda": post["legenda"].strip()}
        print(f"[conteudo] gerado: {post['id']}")
        break
    else:
        print("[conteudo] banco de conteúdo esgotado: adicione posts em conteudo/banco.yaml")
        estado["fila"] = None
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1))


def publicar():
    from .publishers import instagram_publicar, instagram_publicar_reel

    if not os.environ.get("INSTAGRAM_TOKEN"):
        sys.exit("Instagram não configurado.")
    _, estado = carregar()
    item = estado.get("fila")
    if not item:
        print("Nada na fila.")
        return
    base = f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/" \
           f"{os.environ.get('GITHUB_REF_NAME', 'main')}/arts/"
    media = None
    if item.get("video") and (ARTS / item["video"]).exists():
        try:
            media = instagram_publicar_reel(ARTS / item["video"], item["legenda"])
            print(f"[conteudo] reel publicado: {item['id']} → {media}")
        except Exception as e:
            print(f"[aviso] reel falhou, publicando como imagem: {e}")
    if not media:
        media = instagram_publicar(base + item["arquivo"], item["legenda"])
        print(f"[conteudo] feed publicado: {item['id']} → {media}")
    try:
        instagram_publicar(base + item["story"], story=True)
        print("[conteudo] story publicado")
    except Exception as e:  # story é bônus: não impede o post do feed
        print(f"[aviso] story não publicado: {e}")
    estado["publicados"].append(item["id"])
    estado["fila"] = None
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=1))


def previa(cfg):
    banco, _ = carregar()
    out = RAIZ / "preview" / "conteudo"
    hoje = datetime.now(BR).date()
    for i, post in enumerate(banco, 1):
        img = arte(cfg, post, hoje)
        if img is None:
            continue
        salvar(img, out / f"{i:02d}_{post['id']}.jpg")
        if i == 1:
            salvar(story(cfg, img), out / f"{i:02d}_{post['id']}_story.jpg")
    print(f"Prévias em {out}")


def destaques(cfg):
    """Capas dos destaques (1080x1920; o Instagram usa o círculo do centro)."""
    c = cfg["cores"]
    out = RAIZ / "preview" / "destaques"
    for nome in ["OFERTAS", "CUPONS", "COMO FUNCIONA", "TELEGRAM", "DICAS", "BLACK FRIDAY"]:
        img = Image.new("RGB", (1080, 1920), c["fundo"])
        d = ImageDraw.Draw(img)
        d.ellipse((240, 660, 840, 1260), fill=c["fundo2"])
        h = 300
        x, y = 540 - h * 0.3, 960 - h / 2 - 40
        w = h * 0.6
        pts = [(x + w * .55, y), (x, y + h * .58), (x + w * .45, y + h * .58),
               (x + w * .3, y + h), (x + w, y + h * .38), (x + w * .55, y + h * .38)]
        d.polygon(pts, fill=c["destaque"])
        tam = 56 if len(nome) <= 8 else 40
        d.text((540, 1170), nome, font=ImageFont_(900, tam), fill=c["texto"], anchor="mm")
        salvar(img, out / f"destaque_{nome.lower().replace(' ', '_')}.jpg")
    print(f"Capas em {out}")


def main():
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text())
    if "--gerar" in sys.argv:
        gerar(cfg)
    elif "--publicar" in sys.argv:
        publicar()
    elif "--destaques" in sys.argv:
        destaques(cfg)
    else:
        previa(cfg)


if __name__ == "__main__":
    main()
