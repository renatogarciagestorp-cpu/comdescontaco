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
def legenda_telegram(cfg, p, link) -> str:
    nome = html.escape(p.nome)
    economia = p.preco_antigo - p.preco
    topo = "⚡ <b>OFERTA RELÂMPAGO</b> ⚡" if p.desconto >= 50 else "🔥 <b>ACHADO DO DIA</b>"
    linhas = [
        topo,
        "",
        f"🛍️ <b>{nome}</b>",
        "",
        f"❌ De <s>{brl(p.preco_antigo)}</s>" if p.preco_antigo > p.preco else None,
        f"✅ Por <b>{brl(p.preco)}</b>  🔻{p.desconto}% OFF",
        f"💰 Você economiza <b>{brl(economia)}</b>" if economia >= 1 else None,
        f"⭐ {p.nota:.1f} • {mil(p.vendas)} vendidos".replace(".", ",", 1),
        "",
        f"👉 <a href=\"{html.escape(link)}\"><b>COMPRAR AGORA</b></a>",
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
    return "\n".join([
        "💬 Comente QUERO que eu te mando o link no direct!",
        "",
        f"🔥 {p.nome}",
        f"De {brl(p.preco_antigo)} por {brl(p.preco)} (-{p.desconto}%)",
        f"⭐ {p.nota:.1f} • {mil(p.vendas)} vendidos".replace(".", ",", 1),
        "",
        f"📲 Ofertas relâmpago o dia todo no nosso Telegram: {ch['arroba_telegram']} (link na bio)",
        "",
        f"#publi {ch['aviso_afiliado']}",
        "#promoção #achadinhos #shopee #ofertas #desconto #cupom #comdescontaco",
    ])


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
