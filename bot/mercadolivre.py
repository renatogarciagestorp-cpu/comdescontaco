"""Mercado Livre (semiautomático): você manda os links de afiliado para o bot no Telegram (chat privado)
e o robô monta a arte, o Reel e o Story e publica.

Formato da mensagem (um ou vários links; o preço manual é opcional):
    https://mercadolivre.com/sec/abc123
    https://mercadolivre.com/sec/xyz789 de 199,90 por 99,90
Também aceita FOTO com legenda (link + preços), se a página do produto não puder ser lida.

Segurança: só o dono (segredo TELEGRAM_ADMIN_ID) pode mandar links. Para descobrir o seu ID,
mande /start para o bot: ele responde com o número.
"""
import hashlib
import html
import json
import os
import re
from io import BytesIO

import requests
from PIL import Image

from .shopee import Produto

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
RE_URL = re.compile(r"https?://\S*(?:mercadolivre|mercadolibre|meli\.la)\S*", re.I)
RE_DE_POR = re.compile(r"de\s*R?\$?\s*([\d.]+,\d{2}|[\d.]+)\s*por\s*R?\$?\s*([\d.]+,\d{2}|[\d.]+)", re.I)
RE_POR = re.compile(r"\bpor\s*R?\$?\s*([\d.]+,\d{2}|[\d.]+)", re.I)


def _api(metodo):
    return f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{metodo}"


def responder(chat_id, texto):
    try:
        requests.post(_api("sendMessage"), data={"chat_id": chat_id, "text": texto,
                                                 "disable_web_page_preview": "true"}, timeout=30)
    except Exception as e:
        print(f"[ml] não consegui responder no Telegram: {e}")


def numero_br(txt: str) -> float:
    """'1.299,90' -> 1299.90 ; '99.90' -> 99.90"""
    txt = txt.strip()
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".")
    return float(txt)


# ---------------- leitura da página do produto ----------------
def _metas(pagina: str) -> dict:
    out = {}
    for tag in re.findall(r"<meta\b[^>]*>", pagina, re.I):
        attrs = dict(re.findall(r'([\w:-]+)\s*=\s*"([^"]*)"', tag))
        chave = attrs.get("property") or attrs.get("name") or attrs.get("itemprop")
        if chave and "content" in attrs and chave not in out:
            out[chave] = html.unescape(attrs["content"])
    return out


def _jsonld(pagina: str):
    for bloco in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', pagina, re.S | re.I):
        try:
            dado = json.loads(bloco)
        except Exception:
            continue
        for d in (dado if isinstance(dado, list) else [dado]):
            if isinstance(d, dict) and d.get("@type") in ("Product", "product"):
                yield d


def ler_pagina(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"},
                     timeout=30, allow_redirects=True)
    r.raise_for_status()
    pg, final = r.text, r.url
    return extrair(pg, final)


RE_REAIS = r"([\d.]+)\s*reais(?:\s*com\s*(\d+)\s*centavos)?"


def _reais(inteiro, centavos):
    return float(inteiro.replace(".", "")) + int(centavos or 0) / 100


def extrair(pg: str, final: str) -> dict:
    """Lê nome, foto e preços de uma página de produto OU da vitrine de afiliado (/social/...),
    que mostra o produto recomendado em destaque e outros produtos abaixo."""
    m = _metas(pg)
    titulo = m.get("og:title", "")
    info = {"url_final": final, "imagem": m.get("og:image", "")}

    # Vitrine: o título termina com " - R$ 55" (ou "R$ 55,30") = preço do produto em destaque
    mp = re.search(r"\s*-\s*R\$\s*([\d.]+(?:,\d{1,2})?)\s*$", titulo)
    if mp:
        info["preco"] = numero_br(mp.group(1))
        titulo = titulo[:mp.start()]
    info["nome"] = re.sub(r"\s*[|-]\s*Mercado Livre.*$", "", titulo).strip()

    for prod in _jsonld(pg):  # página de produto comum
        info["nome"] = info["nome"] or prod.get("name", "")
        img = prod.get("image")
        info["imagem"] = info["imagem"] or (img[0] if isinstance(img, list) else img or "")
        ofertas = prod.get("offers") or {}
        if isinstance(ofertas, list):
            ofertas = ofertas[0] if ofertas else {}
        if ofertas.get("price") and "preco" not in info:
            info["preco"] = float(ofertas["price"])
        nota = prod.get("aggregateRating") or {}
        if nota.get("ratingValue"):
            info["nota"] = float(nota["ratingValue"])
        break

    # Pares "Antes: X" -> "Agora: Y": usa o par cujo "Agora" bate com o preço do destaque
    pares = re.findall(r"Antes:\s*" + RE_REAIS + r".{0,900}?Agora:\s*" + RE_REAIS, pg, re.S)
    escolhido = None
    for a1, a2, n1, n2 in pares:
        antes, agora = _reais(a1, a2), _reais(n1, n2)
        if "preco" not in info or abs(agora - info["preco"]) < 0.02:
            escolhido = (antes, agora)
            break
    if escolhido:
        info["preco_antigo"] = escolhido[0]
        info.setdefault("preco", escolhido[1])
    if "preco" not in info:
        agora = re.search(r"Agora:\s*" + RE_REAIS, pg)
        if agora:
            info["preco"] = _reais(agora.group(1), agora.group(2))
    if "preco" not in info and m.get("price"):
        info["preco"] = float(m["price"])

    if "/social/" not in final:  # só confia nesses dados na página do próprio produto
        vend = re.search(r"\+?\s*([\d.]+)\s*(mil)?\s*vendidos", pg)
        if vend:
            info["vendas"] = int(float(vend.group(1).replace(".", "")) * (1000 if vend.group(2) else 1))
    mlb = re.search(r"(MLB-?\d{6,})", final) or re.search(r"(MLB-?\d{6,})", info["imagem"])
    info["id"] = (mlb.group(1).replace("-", "") if mlb else
                  hashlib.md5((info["nome"] or final).encode()).hexdigest()[:12])
    return info


def _baixar_foto_telegram(file_id) -> Image.Image:
    caminho = requests.get(_api("getFile"), params={"file_id": file_id}, timeout=30).json()["result"]["file_path"]
    url = f"https://api.telegram.org/file/bot{os.environ['TELEGRAM_BOT_TOKEN']}/{caminho}"
    return Image.open(BytesIO(requests.get(url, timeout=60).content)).convert("RGB")


def montar_produto(link: str, texto: str, foto=None, exigir_desconto=True) -> Produto:
    """Junta o que veio da página com o que você escreveu na mensagem (o manual tem prioridade)."""
    info = {}
    try:
        info = ler_pagina(link)
    except Exception as e:
        print(f"[ml] página não lida ({e}); usando só os dados da mensagem")

    m = RE_DE_POR.search(texto)
    if m:
        info["preco_antigo"], info["preco"] = numero_br(m.group(1)), numero_br(m.group(2))
    else:
        m = RE_POR.search(texto)
        if m:
            info["preco"] = numero_br(m.group(1))
    sobra = RE_DE_POR.sub("", RE_URL.sub("", texto)).strip(" \n-|")
    if len(sobra) > 8 and not info.get("nome"):
        info["nome"] = sobra.splitlines()[0][:120]

    imagem = foto or info.get("imagem")
    if not info.get("preco") or not imagem or not info.get("nome"):
        faltou = [n for n, v in (("preço", info.get("preco")), ("foto", imagem), ("nome", info.get("nome"))) if not v]
        raise ValueError("não consegui ler " + ", ".join(faltou))

    preco = info["preco"]
    antigo = info.get("preco_antigo") or preco
    if antigo < preco:
        antigo = preco
    desconto = round((1 - preco / antigo) * 100) if antigo > preco else 0
    if exigir_desconto and desconto <= 0:
        valor = f"R$ {preco:.2f}".replace(".", ",")
        raise ValueError(f"este produto está SEM desconto no Mercado Livre agora (só {valor}, sem preço "
                         "antigo para mostrar). Escolha um produto com '% OFF' no painel de afiliados")
    return Produto(
        id="ML" + str(info.get("id") or hashlib.md5(link.encode()).hexdigest()[:12]),
        nome=info["nome"], imagem=imagem, link=link, link_original=link,
        preco=preco, preco_antigo=antigo, desconto=int(desconto),
        vendas=int(info.get("vendas") or 0), nota=float(info.get("nota") or 0),
        comissao=0.0, loja="Mercado Livre", plataforma="Mercado Livre",
    )


# ---------------- leitura das mensagens do bot ----------------
def novos_pedidos(state: dict):
    """Lê as mensagens novas do chat privado e devolve [(chat_id, link, texto, foto)]."""
    admin = os.environ.get("TELEGRAM_ADMIN_ID", "").strip()
    offset = state.get("telegram_offset", 0)
    r = requests.get(_api("getUpdates"), params={"offset": offset, "timeout": 0,
                                                "allowed_updates": json.dumps(["message"])}, timeout=60).json()
    pedidos = []
    for upd in r.get("result", []):
        state["telegram_offset"] = upd["update_id"] + 1
        msg = upd.get("message") or {}
        chat = msg.get("chat", {})
        if chat.get("type") != "private":
            continue
        remetente = str(msg.get("from", {}).get("id", ""))
        texto = msg.get("text") or msg.get("caption") or ""
        if not admin:
            responder(chat["id"], f"Olá! Seu ID do Telegram é {remetente}.\n"
                                  "Cadastre-o no GitHub como o segredo TELEGRAM_ADMIN_ID para eu aceitar seus links.")
            continue
        if remetente != admin:
            responder(chat["id"], "Este bot é privado. 🙂 Acompanhe as ofertas no canal @comdescontaco!")
            continue
        if texto.strip().startswith("/start") or texto.strip().startswith("/ajuda"):
            responder(chat["id"], "Mande os links de afiliado do Mercado Livre (um por linha). "
                                  "Opcional: 'de 199,90 por 99,90' depois do link. "
                                  "Eu publico no Telegram e no Instagram em até 10 minutos. ⚡")
            continue
        foto = None
        if msg.get("photo"):
            try:
                foto = _baixar_foto_telegram(msg["photo"][-1]["file_id"])
            except Exception as e:
                print(f"[ml] foto não baixada: {e}")
        links = RE_URL.findall(texto)
        if not links:
            responder(chat["id"], "Não encontrei nenhum link do Mercado Livre nessa mensagem. 🤔")
            continue
        for linha in texto.splitlines() or [texto]:
            for link in RE_URL.findall(linha):
                pedidos.append((chat["id"], link.rstrip(").,"), linha if len(links) > 1 else texto, foto))
    return pedidos
