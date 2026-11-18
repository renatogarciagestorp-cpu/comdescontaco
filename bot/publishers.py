"""Textos e publicação no Telegram e Instagram."""
import html
import json
import os
import re
import time

import requests

from .art import brl, mil

# Palavras que poluem títulos da Shopee e aumentam a carga cognitiva
_RUIDO = re.compile(
    r"\b(promo[çc][ãa]o|oferta|envio imediato|pronta entrega|frete gr[áa]tis|lan[çc]amento|"
    r"original|novo|nova|top|barato|atacado|super)\b|[\[\]【】()|/]+", re.I)


def limpar_titulo(nome: str, max_palavras: int = 9) -> str:
    t = _RUIDO.sub(" ", nome)
    t = re.sub(r"[^\w\s.,+%-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip(" -,.")
    palavras = t.split()[:max_palavras]
    if sum(1 for w in palavras if w.isupper() and len(w) > 3) > len(palavras) / 2:
        palavras = [w.capitalize() for w in palavras]  # TUDO MAIÚSCULO cansa a leitura
    return " ".join(palavras)


# ---------------- Textos ----------------
def _gancho_preco(p, html_ok=True):
    """Primeira linha da legenda: a diferença de preço, que é o que faz parar e clicar."""
    b = (lambda t: f"<b>{t}</b>") if html_ok else (lambda t: t)
    risca = (lambda t: f"<s>{t}</s>") if html_ok else (lambda t: t)
    economia = p.preco_antigo - p.preco
    if p.desconto > 0 and economia >= 1:
        return [f"💥 {b('DE')} {risca(brl(p.preco_antigo))} {b('POR ' + brl(p.preco))}",
                f"📉 {b(str(p.desconto) + '% OFF')} • você economiza {b(brl(economia))}"]
    return [f"💥 {b('SÓ ' + brl(p.preco))}"]


def legenda_telegram(cfg, p, link) -> str:
    nome = html.escape(p.nome)
    selo = "⚡ OFERTA RELÂMPAGO" if p.desconto >= 50 else "🔥 ACHADO DO DIA"
    prova = " • ".join(x for x in (
        f"⭐ {p.nota:.1f}".replace(".", ",") if p.nota else "",
        f"{mil(p.vendas)} vendidos" if p.vendas else "") if x)
    linhas = [
        *_gancho_preco(p),
        "",
        f"<b>{selo}</b>",
        f"🛍️ {nome}",
        prova or None,
        f"🏬 {p.plataforma}",
        "",
        f"👉 <a href=\"{html.escape(link)}\"><b>COMPRAR AGORA</b></a>",
        f"🔗 {html.escape(link)}",
        "",
        "<i>⏳ Preço e estoque podem mudar a qualquer momento.</i>",
    ]
    return "\n".join(l for l in linhas if l is not None)


def legenda_campanha(cfg, c, link) -> str:
    return "\n".join([
        "🎟️ <b>CUPONS LIBERADOS NA SHOPEE</b>",
        "",
        f"⚡ {html.escape(c.nome)}",
        "",
        "Pegue os cupons antes que acabem 👇",
        f"👉 <a href=\"{html.escape(link)}\"><b>PEGAR MEUS CUPONS</b></a>",
    ])


def legenda_instagram(cfg, p) -> str:
    ch = cfg["canal"]
    prova = " • ".join(x for x in (
        f"⭐ {p.nota:.1f}".replace(".", ",") if p.nota else "",
        f"{mil(p.vendas)} vendidos" if p.vendas else "") if x)
    return "\n".join(l for l in [
        *_gancho_preco(p, html_ok=False),
        "💬 Comente QUERO que eu te mando o link no direct!",
        "",
        f"🛍️ {p.nome}",
        prova or None,
        f"🏬 {p.plataforma}",
        "",
        f"📲 Ofertas relâmpago o dia todo no nosso Telegram: {ch['arroba_telegram']} (link na bio)",
        "",
        f"#publi {ch['aviso_afiliado']}",
        "#promoção #achadinhos #" + p.plataforma.lower().replace(" ", "") + " #ofertas #desconto #cupom #comdescontaco",
    ] if l is not None)


# ---------------- Telegram ----------------
def telegram_enviar_foto(caminho_img, legenda, botao_texto, botao_link, sem_som=False):
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    with open(caminho_img, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={
                "chat_id": chat,
                "caption": legenda,
                "parse_mode": "HTML",
                "disable_notification": "true" if sem_som else "false",
                "reply_markup": json.dumps(
                    {"inline_keyboard": [[{"text": botao_texto, "url": botao_link}]]}),
            },
            files={"photo": f},
            timeout=60,
        )
    if not r.ok:
        raise RuntimeError(f"Telegram: {r.status_code} {r.text}")


# ---------------- Instagram (Graph API) ----------------
# Instagram API com login unificado (token de usuário do sistema, não expira)
IG = "https://graph.facebook.com/v27.0"


def instagram_publicar(url_imagem_publica, legenda="", story=False) -> str:
    """Publica no feed (ou nos Stories, se story=True) e devolve o ID da publicação.
    A imagem precisa de link público."""
    uid, token = os.environ["INSTAGRAM_USER_ID"], os.environ["INSTAGRAM_TOKEN"]
    dados = {"image_url": url_imagem_publica, "access_token": token}
    if story:
        dados["media_type"] = "STORIES"
    else:
        dados["caption"] = legenda
    r = requests.post(f"{IG}/{uid}/media", data=dados, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram media: {r.text}")
    criacao = r.json()["id"]
    for _ in range(12):  # aguarda o Instagram processar a imagem
        st = requests.get(f"{IG}/{criacao}", params={
            "fields": "status_code", "access_token": token}, timeout=30).json()
        if st.get("status_code") == "FINISHED":
            break
        time.sleep(5)
    r = requests.post(f"{IG}/{uid}/media_publish", data={
        "creation_id": criacao, "access_token": token}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram publish: {r.text}")
    return r.json()["id"]


def instagram_publicar_reel(caminho_video, legenda, cover_url=None) -> str:
    """Publica um Reel (aparece também no feed) enviando o arquivo direto para a Meta
    (upload resumable): não precisa de link público para o vídeo."""
    uid, token = os.environ["INSTAGRAM_USER_ID"], os.environ["INSTAGRAM_TOKEN"]
    dados = {"media_type": "REELS", "upload_type": "resumable", "caption": legenda,
             "share_to_feed": "true", "access_token": token}
    if cover_url:  # capa do Reel = arte do post (aparece no perfil e no feed)
        dados["cover_url"] = cover_url
    r = requests.post(f"{IG}/{uid}/media", data=dados, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram reel (container): {r.text}")
    criacao = r.json()["id"]
    dados = open(caminho_video, "rb").read()
    versao = IG.rsplit("/", 1)[-1]
    up = requests.post(f"https://rupload.facebook.com/ig-api-upload/{versao}/{criacao}", data=dados,
                       headers={"Authorization": f"OAuth {token}", "offset": "0",
                                "file_size": str(len(dados))}, timeout=300)
    if not up.ok:
        raise RuntimeError(f"Instagram reel (upload): {up.text}")
    for _ in range(40):  # vídeo demora mais para processar (até ~3 min)
        st = requests.get(f"{IG}/{criacao}", params={
            "fields": "status_code,status", "access_token": token}, timeout=30).json()
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram reel (processamento): {st.get('status')}")
        time.sleep(5)
    r = requests.post(f"{IG}/{uid}/media_publish", data={
        "creation_id": criacao, "access_token": token}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram reel (publicar): {r.text}")
    return r.json()["id"]


# ---------------- Página do Facebook ----------------
_TOKEN_PAGINA = {}


def facebook_ativo() -> bool:
    return bool(os.environ.get("FB_PAGE_ID") and os.environ.get("FB_TOKEN"))


def _token_pagina():
    """Aceita o token da Página ou o de um usuário do sistema (que nunca expira): neste caso,
    busca o token da Página a partir dele."""
    if "t" not in _TOKEN_PAGINA:
        pid, tok = os.environ["FB_PAGE_ID"], os.environ["FB_TOKEN"]
        r = requests.get(f"{IG}/{pid}", params={"fields": "access_token", "access_token": tok}, timeout=30)
        _TOKEN_PAGINA["t"] = (r.json().get("access_token") if r.ok else None) or tok
    return _TOKEN_PAGINA["t"]


def facebook_publicar_foto(url_imagem_publica, mensagem) -> str:
    """Publica uma foto com legenda na Página (links na legenda ficam clicáveis)."""
    r = requests.post(f"{IG}/{os.environ['FB_PAGE_ID']}/photos", data={
        "url": url_imagem_publica, "message": mensagem, "published": "true",
        "access_token": _token_pagina()}, timeout=90)
    if not r.ok:
        raise RuntimeError(f"Facebook: {r.text}")
    return r.json().get("post_id") or r.json().get("id")


def legenda_facebook(cfg, p, link) -> str:
    ch = cfg["canal"]
    selo = "⚡ OFERTA RELÂMPAGO" if p.desconto >= 50 else "🔥 ACHADO DO DIA"
    prova = " • ".join(x for x in (
        f"⭐ {p.nota:.1f}".replace(".", ",") if p.nota else "",
        f"{mil(p.vendas)} vendidos" if p.vendas else "") if x)
    return "\n".join(l for l in [
        *_gancho_preco(p, html_ok=False),
        "",
        selo,
        f"🛍️ {p.nome}",
        prova or None,
        f"🏬 {p.plataforma}",
        "",
        f"👉 COMPRAR AGORA: {link}",
        "",
        f"📲 Ofertas relâmpago o dia todo no Telegram: {ch['link_telegram']}",
        "⏳ Preço e estoque podem mudar a qualquer momento.",
        f"#publi {ch['aviso_afiliado']}",
    ] if l is not None)
