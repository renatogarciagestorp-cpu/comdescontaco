"""Ciclo do bot: busca ofertas → filtra → gera arte → publica.

Uso:
  python -m bot.main            # execução real (usa os segredos do GitHub)
  python -m bot.main --demo     # gera artes de exemplo em preview/, sem publicar nada
  python -m bot.main --instagram  # publica a fila do Instagram (roda depois do git push)
"""
import json
import math
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from . import publishers as pub
from .art import gerar_arte, salvar

RAIZ = Path(__file__).resolve().parent.parent
STATE = RAIZ / "data" / "state.json"
FILA_IG = RAIZ / "data" / "instagram_queue.json"
ARTS = RAIZ / "arts"
BR = ZoneInfo("America/Sao_Paulo")


def carregar(p, padrao):
    return json.loads(p.read_text()) if p.exists() else padrao


def gravar(p, dados):
    p.write_text(json.dumps(dados, ensure_ascii=False, indent=1))


def pontuar(p) -> float:
    """Desconto pesa mais; vendas e nota dão confiança; comissão desempata."""
    return p.desconto * 1.0 + math.log10(max(p.vendas, 1)) * 8 + (p.nota - 4) * 15 + p.comissao * 20


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

    agora = datetime.now(BR)
    ini, fim = cfg["publicacao"]["horario_silencioso"]
    if ini <= agora.hour < fim and "--forcar" not in sys.argv:
        print(f"Horário silencioso ({agora:%H:%M}). Nada a fazer.")
        return

    api, state = ShopeeAPI(), carregar(STATE, {})
    state.setdefault("produtos", {}); state.setdefault("campanhas", {})
    state.setdefault("ultima_campanha", 0); state.setdefault("instagram", {"dia": "", "qtd": 0})
    pc = cfg["publicacao"]

    # 1) Campanha/cupom oficial da Shopee de tempos em tempos
    if time.time() - state["ultima_campanha"] > pc["campanha_shopee_a_cada_horas"] * 3600:
        try:
            for c in api.buscar_campanhas():
                if c.id in state["campanhas"]:
                    continue
                link = api.link_rastreado(c.link, "telegram") or c.link
                arte = gerar_arte(cfg, c.nome, c.imagem, selo="CUPONS", rodape="TOQUE NO LINK")
                caminho = salvar(arte, ARTS / f"camp_{abs(hash(c.id)) % 10**9}.jpg")
                pub.telegram_enviar_foto(caminho, pub.legenda_campanha(cfg, c, link),
                                         "🎟️ Pegar cupons", link)
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
            selo = "IMPERDÍVEL" if p.desconto >= 50 else "OFERTA"
            arte = gerar_arte(cfg, p.nome, p.imagem, p.preco, p.preco_antigo, p.desconto, selo=selo)
            caminho = salvar(arte, ARTS / f"{p.id}.jpg")
            link = api.link_rastreado(p.link_original, "telegram") or p.link
            pub.telegram_enviar_foto(caminho, pub.legenda_telegram(cfg, p, link), "🛒 Comprar agora", link)
            state["produtos"][p.id] = time.time()
            postados += 1
            print(f"[postado] -{p.desconto}% {p.nome[:60]}")
            # os melhores do dia também vão para o Instagram
            if state["instagram"]["qtd"] < pc["instagram_posts_por_dia"] and p.desconto >= 40:
                fila_ig.append({"arquivo": caminho.name, "legenda": pub.legenda_instagram(cfg, p)})
                state["instagram"]["qtd"] += 1
            if postados < pc["posts_por_execucao"]:
                time.sleep(pc["intervalo_segundos_entre_posts"])
        except Exception as e:
            print(f"[erro post {p.id}] {e}")

    # esquece produtos antigos para o arquivo não crescer
    corte = time.time() - 30 * 86400
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
    fila = carregar(FILA_IG, [])
    restantes = []
    for item in fila:
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/arts/{item['arquivo']}"
        try:
            pub.instagram_publicar(url, item["legenda"])
            print(f"[instagram] {item['arquivo']}")
        except Exception as e:
            print(f"[erro instagram] {e}")
            if (ARTS / item["arquivo"]).exists():
                restantes.append(item)
    gravar(FILA_IG, restantes)


def demo(cfg):
    """Gera artes com produtos fictícios para ver o visual, sem API nenhuma."""
    from PIL import Image, ImageDraw
    from .shopee import Campanha, Produto

    def foto(cor):
        im = Image.new("RGB", (600, 600), "#F3F3F3")
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((150, 120, 450, 480), radius=60, fill=cor)
        d.ellipse((240, 200, 360, 320), fill="#FFFFFF")
        return im

    exemplos = [
        Produto("1", "Fone de Ouvido Bluetooth 5.3 TWS com Cancelamento de Ruído e Case Carregador",
                foto("#222222"), "https://s.shopee.com.br/x", "", 47.90, 159.90, 70, 12850, 4.8, 0.08, "Loja"),
        Produto("2", "Air Fryer 4L Digital Antiaderente 1500W", foto("#B0B0B0"),
                "https://s.shopee.com.br/x", "", 289.00, 449.00, 36, 3420, 4.9, 0.05, "Loja"),
    ]
    out = RAIZ / "preview"
    for p in exemplos:
        selo = "IMPERDÍVEL" if p.desconto >= 50 else "OFERTA"
        salvar(gerar_arte(cfg, p.nome, p.imagem, p.preco, p.preco_antigo, p.desconto, selo=selo),
               out / f"produto_{p.id}.jpg")
        (out / f"produto_{p.id}_telegram.txt").write_text(pub.legenda_telegram(cfg, p, p.link))
        (out / f"produto_{p.id}_instagram.txt").write_text(pub.legenda_instagram(cfg, p))
    c = Campanha("c", "11.11 — Cupons de até R$ 50 OFF + Frete Grátis", foto("#EE4D2D"), "https://s.shopee.com.br/x", 0)
    salvar(gerar_arte(cfg, c.nome, c.imagem, selo="CUPONS", rodape="TOQUE NO LINK"), out / "campanha.jpg")
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
