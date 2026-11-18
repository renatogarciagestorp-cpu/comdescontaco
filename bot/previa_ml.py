"""Prévia privada: gera a arte e o Reel de um link do Mercado Livre e manda só para o dono do bot
(TELEGRAM_ADMIN_ID). Nada é publicado no canal nem no Instagram."""
import json
import os
import sys
from pathlib import Path

import requests
import yaml

from .art import arte_produto, salvar
from .mercadolivre import montar_produto
from .publishers import legenda_instagram, legenda_telegram, limpar_titulo
from .video import renderizar, roteiro_oferta

RAIZ = Path(__file__).resolve().parent.parent


def main():
    url, texto = sys.argv[1], " ".join(sys.argv[2:])
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text())
    p = montar_produto(url, texto)
    p = p.__class__(**{**p.__dict__, "nome": limpar_titulo(p.nome)})
    out = RAIZ / "preview"
    tg = salvar(arte_produto(cfg, p, "telegram"), out / "previa_telegram.jpg")
    ig = salvar(arte_produto(cfg, p, "instagram"), out / "previa_instagram.jpg")
    reel = renderizar(roteiro_oferta(cfg, p), out / "previa_reel.mp4")
    api = f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}"
    chat = os.environ["TELEGRAM_ADMIN_ID"]
    legenda = f"👀 PRÉVIA (não publicada)\n{p.nome}\n{p.preco:.2f}".replace(".", ",")
    envios = ((tg, "Arte do Telegram", "👀 PRÉVIA DO CANAL (não publicada)\n\n" + legenda_telegram(cfg, p, url), "HTML"),
              (ig, "Arte do Instagram", "👀 PRÉVIA DO INSTAGRAM (não publicada)\n\n" + legenda_instagram(cfg, p), None))
    for arq, nome, texto, modo in envios:
        dados = {"chat_id": chat, "caption": texto[:1024]}
        if modo:  # prévia do canal: igual ao post real, com o botão de compra
            dados["parse_mode"] = modo
            dados["reply_markup"] = json.dumps({"inline_keyboard": [[{"text": "🛒 COMPRAR AGORA", "url": url}]]})
        with open(arq, "rb") as f:
            r = requests.post(f"{api}/sendPhoto", data=dados, files={"photo": f}, timeout=60)
        print(nome, r.status_code, r.text[:120])
    with open(reel, "rb") as f:
        r = requests.post(f"{api}/sendVideo", data={"chat_id": chat, "caption": f"{legenda}\nReel (só Instagram)"},
                          files={"video": f}, timeout=120)
    print("Reel", r.status_code, r.text[:120])


if __name__ == "__main__":
    main()
