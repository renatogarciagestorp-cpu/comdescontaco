"""Ciclo do bot: busca ofertas → filtra → gera arte → publica.

Uso:
  python -m bot.main              # execução real (usa os segredos do GitHub)
  python -m bot.main --demo       # gera artes de exemplo em preview/, sem publicar nada
  python -m bot.main --instagram  # publica a fila do Instagram (roda depois do git push)
"""
import json
import math
import os
import random
import sys
import time
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import publishers as pub
from .art import arte_campanha, arte_produto, salvar

RAIZ = Path(__file__).resolve().parent.parent
STATE = RAIZ / "data" / "state.json"
FILA_IG = RAIZ / "data" / "instagram_queue.json"
LINKS_IG = RAIZ / "data" / "instagram_links.json"  # lido pelo robô de comentários
ARTS = RAIZ / "arts"
BR = ZoneInfo("America/Sao_Paulo")


def carregar(p, padrao):
    return json.loads(p.read_text()) if p.exists() else padrao


def gravar(p, dados):
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=1))


def pontuar(p) -> float:
    """Desconto pesa mais; vendas e nota dão confiança; comissão desempata."""
    return p.desconto + math.log10(max(p.vendas, 1)) * 8 + (p.nota - 4) * 15 + p.comissao * 20


def escolher(produtos, cfg, state):
    f = cfg["filtros"]
    limite = time.time() - f["repetir_produto_apos_dias"] * 86400
    vistos, bons = set(), []
    for p in produtos:
        if p.id in vistos or state["produtos"].get(p.id, 0) > limite:
            continue
        vistos.add(p.id)
        if (p.desconto >= f["desconto_minimo"] and p.nota >= f["nota_minima"]
                and p.vendas >= f["vendas_minimas"] and p.preco <= f["preco_maximo"]):
            bons.append(p)
    return sorted(bons, key=pontuar, reverse=True)


def limpar_artes(dias=3):
    for a in ARTS.glob("*.jpg"):
        if a.stat().st_mtime < time.time() - dias * 86400:
            a.unlink()


def ciclo(cfg):
    from .shopee import ShopeeAPI

    faltando = [k for k in ("SHOPEE_APP_ID", "SHOPEE_SECRET", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
                if not os.environ.get(k)]
    if faltando:
        print(f"Aguardando configuração. Segredos ainda não cadastrados: {', '.join(faltando)}")
        return

    agora = datetime.now(BR)
    faixa = cfg["publicacao"].get("madrugada_sem_som") or []
    sem_som = bool(faixa) and faixa[0] <= agora.hour < faixa[1]

    api, state = ShopeeAPI(), carregar(STATE, {})
    for k, v in {"produtos": {}, "campanhas": {}, "ultima_campanha": 0,
                 "instagram": {"dia": "", "qtd": 0}}.items():
        state.setdefault(k, v)
    pc = cfg["publicacao"]

    # 1) Campanha/cupom oficial da Shopee de tempos em tempos
    if time.time() - state["ultima_campanha"] > pc["campanha_shopee_a_cada_horas"] * 3600:
        try:
            for c in api.buscar_campanhas():
                if c.id in state["campanhas"]:
                    continue
                link = api.link_rastreado(c.link, "telegram") or c.link
                horas = (c.fim - time.time()) / 3600 if c.fim else None
                caminho = salvar(arte_campanha(cfg, c.nome, c.imagem, horas),
                                 ARTS / f"camp_{int(time.time())}.jpg")
                pub.telegram_enviar_foto(caminho, pub.legenda_campanha(cfg, c, link),
                                         "🎟️ PEGAR MEUS CUPONS", link, sem_som)
                state["campanhas"][c.id] = time.time()
                print(f"[campanha] {c.nome}")
                break
        except Exception as e:
            print(f"[erro campanha] {e}")
        state["ultima_campanha"] = time.time()

    # 2) Produtos em promoção
    palavras = random.sample(cfg["busca"]["palavras_chave"], cfg["busca"]["palavras_por_execucao"])
    produtos = []
    for kw in palavras:
        try:
            produtos += api.buscar_produtos(kw, cfg["busca"]["resultados_por_palavra"])
        except Exception as e:
            print(f"[erro busca '{kw}'] {e}")
    candidatos = escolher(produtos, cfg, state)
    print(f"{len(produtos)} produtos encontrados, {len(candidatos)} passaram nos filtros.")

    hoje = agora.strftime("%Y-%m-%d")
    if state["instagram"]["dia"] != hoje:
        state["instagram"] = {"dia": hoje, "qtd": 0}
    fila_ig = carregar(FILA_IG, [])

    postados = 0
    for p in candidatos:
        if postados >= pc["posts_por_execucao"]:
            break
        try:
            p = replace(p, nome=pub.limpar_titulo(p.nome))
            caminho = salvar(arte_produto(cfg, p, "telegram"), ARTS / f"{p.id}.jpg")
            link = api.link_rastreado(p.link_original, "telegram") or p.link
            pub.telegram_enviar_foto(caminho, pub.legenda_telegram(cfg, p, link),
                                     "🛒 COMPRAR AGORA", link, sem_som)
            state["produtos"][p.id] = time.time()
            postados += 1
            print(f"[postado] -{p.desconto}% {p.nome}")
            # os melhores do dia também vão para o Instagram (arte com "comente QUERO")
            if state["instagram"]["qtd"] < pc["instagram_posts_por_dia"] and p.desconto >= 40:
                arq = salvar(arte_produto(cfg, p, "instagram"), ARTS / f"{p.id}_ig.jpg")
                fila_ig.append({
                    "arquivo": arq.name,
                    "legenda": pub.legenda_instagram(cfg, p),
                    "link": api.link_rastreado(p.link_original, "instagram") or p.link,
                    "nome": p.nome,
                    "preco": pub.brl(p.preco),
                })
                state["instagram"]["qtd"] += 1
            if postados < pc["posts_por_execucao"]:
                time.sleep(pc["intervalo_segundos_entre_posts"])
        except Exception as e:
            print(f"[erro post {p.id}] {e}")

    corte = time.time() - 30 * 86400  # esquece itens antigos para o arquivo não crescer
    state["produtos"] = {k: v for k, v in state["produtos"].items() if v > corte}
    state["campanhas"] = {k: v for k, v in state["campanhas"].items() if v > corte}
    gravar(STATE, state)
    gravar(FILA_IG, fila_ig)
    limpar_artes()


def publicar_instagram():
    """Roda depois do git push, quando as artes já têm link público no GitHub."""
    if not os.environ.get("INSTAGRAM_TOKEN"):
        print("Instagram não configurado; pulando.")
        return
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    fila, links = carregar(FILA_IG, []), carregar(LINKS_IG, {})
    restantes = []
    for item in fila:
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/arts/{item['arquivo']}"
        try:
            media_id = pub.instagram_publicar(url, item["legenda"])
            links[media_id] = {"link": item["link"], "nome": item["nome"],
                               "preco": item["preco"], "ts": int(time.time())}
            print(f"[instagram] {item['arquivo']} → {media_id}")
        except Exception as e:
            print(f"[erro instagram] {e}")
            if (ARTS / item["arquivo"]).exists():
                restantes.append(item)
    corte = time.time() - 30 * 86400
    gravar(LINKS_IG, {k: v for k, v in links.items() if v["ts"] > corte})
    gravar(FILA_IG, restantes)


def demo(cfg):
    """Gera artes com produtos fictícios para ver o visual, sem API nenhuma."""
    from PIL import Image, ImageDraw
    from .shopee import Produto

    def foto(cor):
        im = Image.new("RGB", (800, 800), "#FFFFFF")
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((220, 140, 580, 660), radius=90, fill=cor)
        d.ellipse((330, 250, 470, 390), fill="#FFFFFF")
        return im

    exemplos = [
        Produto("1", "Fone De Ouvido Bluetooth 5.3 TWS PROMOÇÃO Cancelamento de Ruído Envio Imediato [Original]",
                foto("#222222"), "https://s.shopee.com.br/x", "", 47.90, 159.90, 70, 12850, 4.8, 0.08, "Loja"),
        Produto("2", "Air Fryer 4L Digital Antiaderente 1500W Pronta Entrega", foto("#9A9A9A"),
                "https://s.shopee.com.br/x", "", 289.00, 449.00, 36, 3420, 4.9, 0.05, "Loja"),
    ]
    out = RAIZ / "preview"
    for p in exemplos:
        p = replace(p, nome=pub.limpar_titulo(p.nome))
        salvar(arte_produto(cfg, p, "telegram"), out / f"produto_{p.id}_telegram.jpg")
        salvar(arte_produto(cfg, p, "instagram"), out / f"produto_{p.id}_instagram.jpg")
        (out / f"produto_{p.id}_telegram.txt").write_text(pub.legenda_telegram(cfg, p, p.link))
        (out / f"produto_{p.id}_instagram.txt").write_text(pub.legenda_instagram(cfg, p))
    salvar(arte_campanha(cfg, "11.11 Shopee: cupons de até R$ 50 OFF + frete grátis", foto("#EE4D2D"), 5),
           out / "campanha.jpg")
    print(f"Prévias geradas em {out}")


def main():
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text())
    if "--demo" in sys.argv:
        demo(cfg)
    elif "--instagram" in sys.argv:
        publicar_instagram()
    else:
        ciclo(cfg)


if __name__ == "__main__":
    main()
