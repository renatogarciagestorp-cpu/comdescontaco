"""Textos e publicação no Telegram e Instagram."""
import html
import json
import os
import time

import requests

from .art import _brl


# ---------------- Textos ----------------
def legenda_telegram(cfg, p, link) -> str:
    nome = html.escape(p.nome[:120])
    chamada = "🚨 <b>PREÇO DE BLACK!</b>" if p.desconto >= 50 else "🔥 <b>ACHADO DO DIA</b>"
    linhas = [
        chamada,
        "",
        f"🛍️ {nome}",
        "",
        f"❌ <s>{_brl(p.preco_antigo)}</s>" if p.preco_antigo > p.preco else "",
        f"✅ <b>{_brl(p.preco)}</b>  (-{p.desconto}%)",
        f"⭐ {p.nota:.1f}  •  {p.vendas:,} vendidos".replace(",", "."),
        "",
        f"👉 <a href=\"{html.escape(link)}\">Comprar na Shopee</a>",
        "",
        "<i>⚠️ Preço e estoque podem mudar a qualquer momento.</i>",
    ]
    return "\n".join(l for l in linhas if l is not None).replace("\n\n\n", "\n\n")


def legenda_campanha(cfg, c, link) -> str:
    return "\n".join([
        "⚡ <b>CAMPANHA ATIVA NA SHOPEE</b>",
        "",
        f"🎟️ {html.escape(c.nome)}",
        "",
        "Cupons e ofertas relâmpago liberados na página da campanha 👇",
        f"👉 <a href=\"{html.escape(link)}\">Ver ofertas e pegar cupons</a>",
    ])


def legenda_instagram(cfg, p) -> str:
    ch = cfg["canal"]
    return "\n".join([
        f"🔥 {p.nome[:90]}",
        "",
        f"De {_brl(p.preco_antigo)} por {_brl(p.preco)} (-{p.desconto}%)",
        f"⭐ {p.nota:.1f} • {p.vendas:,} vendidos".replace(",", "."),
        "",
        f"🔗 O link desta e de outras ofertas está no nosso canal do Telegram: {ch['arroba_telegram']} (link na bio)",
        "",
        f"#publi {ch['aviso_afiliado']}",
        "#promoção #achadinhos #shopee #ofertas #desconto #cupom #economia",
    ])


# ---------------- Telegram ----------------
def telegram_enviar_foto(caminho_img, legenda, botao_texto, botao_link):
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    with open(caminho_img, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={
                "chat_id": chat,
                "caption": legenda,
                "parse_mode": "HTML",
                "reply_markup": json.dumps(
                    {"inline_keyboard": [[{"text": botao_texto, "url": botao_link}]]}),
            },
            files={"photo": f},
            timeout=60,
        )
    if not r.ok:
        raise RuntimeError(f"Telegram: {r.status_code} {r.text}")


# ---------------- Instagram (Graph API) ----------------
IG = "https://graph.instagram.com/v21.0"


def instagram_publicar(url_imagem_publica, legenda):
    """Publica no feed. A imagem precisa estar num link público (usamos o GitHub)."""
    uid, token = os.environ["INSTAGRAM_USER_ID"], os.environ["INSTAGRAM_TOKEN"]
    r = requests.post(f"{IG}/{uid}/media", data={
        "image_url": url_imagem_publica, "caption": legenda, "access_token": token}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram media: {r.text}")
    criacao = r.json()["id"]
    for _ in range(10):  # aguarda o Instagram processar a imagem
        st = requests.get(f"{IG}/{criacao}", params={
            "fields": "status_code", "access_token": token}, timeout=30).json()
        if st.get("status_code") == "FINISHED":
            break
        time.sleep(5)
    r = requests.post(f"{IG}/{uid}/media_publish", data={
        "creation_id": criacao, "access_token": token}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram publish: {r.text}")
