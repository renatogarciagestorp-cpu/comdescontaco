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
    """Prioriza os MAIORES descontos e os produtos VIRAIS (muitas vendas); nota e comissão desempatam."""
    return p.desconto * 1.2 + math.log10(max(p.vendas, 1)) * 15 + (p.nota - 4) * 10 + p.comissao * 20


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
    for a in [*ARTS.glob("*.jpg"), *ARTS.glob("*.mp4")]:
        if a.stat().st_mtime < time.time() - dias * 86400:
            a.unlink()


def publicar_oferta(cfg, p, link_tg, link_ig, state, fila_ig, sem_som, forcar_instagram=False):
    """Publica uma oferta (Shopee ou Mercado Livre) no Telegram e, se for das melhores, prepara o Instagram."""
    pc = cfg["publicacao"]
    p = replace(p, nome=pub.limpar_titulo(p.nome))
    if os.environ.get("SO_INSTAGRAM") != "true":
        caminho = salvar(arte_produto(cfg, p, "telegram"), ARTS / f"{p.id}.jpg")
        pub.telegram_enviar_foto(caminho, pub.legenda_telegram(cfg, p, link_tg), "🛒 COMPRAR AGORA", link_tg, sem_som)
    state["produtos"][p.id] = time.time()
    print(f"[postado] {p.plataforma} -{p.desconto}% {p.nome}")
    if state["instagram"]["qtd"] >= pc["instagram_posts_por_dia"] or not (forcar_instagram or p.desconto >= 40):
        return
    arq = salvar(arte_produto(cfg, p, "instagram"), ARTS / f"{p.id}_ig.jpg")
    video = None
    if state["instagram"]["qtd"] < cfg.get("instagram", {}).get("reels_ofertas_por_dia", 2):
        try:
            from .video import renderizar, roteiro_oferta
            video = renderizar(roteiro_oferta(cfg, p), ARTS / f"{p.id}_reel.mp4").name
        except Exception as e:
            print(f"[aviso] reel da oferta não gerado: {e}")
    story_arq = None
    if cfg.get("instagram", {}).get("stories_ofertas", True):
        from PIL import Image as _Img
        from .conteudo import story as _story
        titulo = "OFERTA RELÂMPAGO" if p.desconto >= 50 else "ACHADO DO DIA"
        st = _story(cfg, _Img.open(arq), titulo, 'COMENTE "QUERO" NO POST')
        story_arq = salvar(st, ARTS / f"{p.id}_story.jpg").name
    fila_ig.append({"story": story_arq, "video": video, "arquivo": arq.name,
                    "legenda": pub.legenda_instagram(cfg, p), "link": link_ig,
                    "legenda_fb": pub.legenda_facebook(cfg, p, link_tg),
                    "nome": p.nome, "preco": pub.brl(p.preco)})
    state["instagram"]["qtd"] += 1


def ciclo_mercadolivre(cfg, state, fila_ig, sem_som, links=None):
    """Publica os links do Mercado Livre que você mandou para o bot no Telegram
    (ou os passados direto em 'links', pelo workflow "Publicar links do Mercado Livre")."""
    from . import mercadolivre as ml
    if links is not None:
        pedidos = [(None, l.rstrip(").,"), "", None) for l in ml.RE_URL.findall(links)]
    else:
        try:
            pedidos = ml.novos_pedidos(state)
        except Exception as e:
            print(f"[erro ml] leitura do Telegram: {e}")
            return
    for chat_id, link, texto, foto in pedidos:
        try:
            p = ml.montar_produto(link, texto, foto, cfg["filtros"].get("exigir_desconto", True))
            publicar_oferta(cfg, p, link, link, state, fila_ig, sem_som, forcar_instagram=True)
            chat_id and ml.responder(chat_id, f"✅ Publicado: {p.nome[:60]} por {pub.brl(p.preco)}"
                                  + (f" (-{p.desconto}%)" if p.desconto else ""))
            time.sleep(15)
        except Exception as e:
            print(f"[erro ml] {link}: {e}")
            dica = ("" if "SEM desconto" in str(e) else
                    "\nTente de novo com os preços (ex.: 'de 199,90 por 99,90') ou mande uma FOTO "
                    "do produto com o link e os preços na legenda.")
            chat_id and ml.responder(chat_id, f"❌ Não publiquei {link}\nMotivo: {e}.{dica}")


def ciclo(cfg, so_mercadolivre=False, links=None):
    from .shopee import ShopeeAPI

    faltando = [k for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") if not os.environ.get(k)]
    if faltando:
        print(f"Aguardando configuração. Segredos ainda não cadastrados: {', '.join(faltando)}")
        return

    agora = datetime.now(BR)
    faixa = cfg["publicacao"].get("madrugada_sem_som") or []
    sem_som = bool(faixa) and faixa[0] <= agora.hour < faixa[1]

    state = carregar(STATE, {})
    for k, v in {"produtos": {}, "campanhas": {}, "ultima_campanha": 0,
                 "instagram": {"dia": "", "qtd": 0}}.items():
        state.setdefault(k, v)
    pc = cfg["publicacao"]
    hoje = agora.strftime("%Y-%m-%d")
    if state["instagram"]["dia"] != hoje:
        state["instagram"] = {"dia": hoje, "qtd": 0}
    fila_ig = carregar(FILA_IG, [])

    # 1) Mercado Livre: links enviados por você ao bot
    ciclo_mercadolivre(cfg, state, fila_ig, sem_som, links)

    # 2) Shopee: automático (quando as chaves estiverem cadastradas)
    if not cfg["busca"].get("shopee_ativa", True):
        print("Shopee pausada no config.yaml (busca.shopee_ativa: false).")
    elif so_mercadolivre or not (os.environ.get("SHOPEE_APP_ID") and os.environ.get("SHOPEE_SECRET")):
        if not so_mercadolivre:
            print("Shopee ainda não configurada (SHOPEE_APP_ID / SHOPEE_SECRET); pulando.")
    else:
        api = ShopeeAPI()
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

        palavras = random.sample(cfg["busca"]["palavras_chave"], cfg["busca"]["palavras_por_execucao"])
        produtos = []
        for kw in palavras:
            try:
                produtos += api.buscar_produtos(kw, cfg["busca"]["resultados_por_palavra"])
            except Exception as e:
                print(f"[erro busca '{kw}'] {e}")
        candidatos = escolher(produtos, cfg, state)
        print(f"{len(produtos)} produtos encontrados, {len(candidatos)} passaram nos filtros.")
        postados = 0
        for p in candidatos:
            if postados >= pc["posts_por_execucao"]:
                break
            try:
                link_tg = api.link_rastreado(p.link_original, "telegram") or p.link
                link_ig = api.link_rastreado(p.link_original, "instagram") or p.link
                publicar_oferta(cfg, p, link_tg, link_ig, state, fila_ig, sem_som)
                postados += 1
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
    """Roda depois do git push, quando as artes já têm link público no GitHub.
    Publica a fila no Instagram (imagem/Reel + Story) e na Página do Facebook (foto com link)."""
    ig_ok, fb_ok = bool(os.environ.get("INSTAGRAM_TOKEN")), pub.facebook_ativo()
    if not (ig_ok or fb_ok):
        print("Instagram e Facebook não configurados; pulando.")
        return
    repo = os.environ["GITHUB_REPOSITORY"]
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    fila, links = carregar(FILA_IG, []), carregar(LINKS_IG, {})
    restantes = []
    for item in fila:
        url = f"https://raw.githubusercontent.com/{repo}/{branch}/arts/{item['arquivo']}"
        if ig_ok and not item.get("ig_feito"):
            try:
                media_id = None
                if item.get("video") and (ARTS / item["video"]).exists():
                    try:
                        media_id = pub.instagram_publicar_reel(ARTS / item["video"], item["legenda"], url)
                    except Exception as e:
                        print(f"[aviso] reel falhou, publicando imagem: {e}")
                media_id = media_id or pub.instagram_publicar(url, item["legenda"])
                item["ig_feito"] = True
                if item.get("story"):
                    try:
                        surl = f"https://raw.githubusercontent.com/{repo}/{branch}/arts/{item['story']}"
                        pub.instagram_publicar(surl, story=True)
                    except Exception as e:
                        print(f"[aviso] story da oferta não publicado: {e}")
                links[media_id] = {"link": item["link"], "nome": item["nome"],
                                   "preco": item["preco"], "ts": int(time.time())}
                print(f"[instagram] {item['arquivo']} → {media_id}")
            except Exception as e:
                print(f"[erro instagram] {e}")
        if fb_ok and not item.get("fb_feito") and item.get("legenda_fb"):
            try:
                post = pub.facebook_publicar_foto(url, item["legenda_fb"])
                item["fb_feito"] = True
                print(f"[facebook] {item['arquivo']} → {post}")
            except Exception as e:
                print(f"[erro facebook] {e}")
        pendente = (ig_ok and not item.get("ig_feito")) or \
                   (fb_ok and item.get("legenda_fb") and not item.get("fb_feito"))
        if pendente and (ARTS / item["arquivo"]).exists():
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
    elif "--ml" in sys.argv:
        ciclo(cfg, so_mercadolivre=True)
    elif "--links" in sys.argv:
        ciclo(cfg, so_mercadolivre=True, links=os.environ.get("LINKS", ""))
    else:
        ciclo(cfg)


if __name__ == "__main__":
    main()
