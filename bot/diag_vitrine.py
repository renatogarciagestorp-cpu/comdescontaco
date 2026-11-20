"""Diagnóstico da vitrine de afiliado do Mercado Livre (/social/...).

Objetivo: descobrir se dá para ler a vitrine sozinho (lista de produtos) e se os links
dos produtos dentro dela carregam a marcação de afiliado (comissão).
Uso: python -m bot.diag_vitrine <link meli.la>
"""
import json
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests

from .mercadolivre import UA, _metas

H = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}


def mostrar_url(rotulo, url):
    u = urlparse(url)
    print(f"{rotulo}: {u.scheme}://{u.netloc}{u.path}")
    for k, v in parse_qs(u.query).items():
        print(f"    param {k} = {v[0][:80]}")


url = sys.argv[1]
r = requests.get(url, headers=H, timeout=30)
pg = r.text
print("status:", r.status_code, "| tamanho:", len(pg))
for h in r.history:
    mostrar_url("  redirecionou de", h.url)
mostrar_url("FINAL", r.url)

m = _metas(pg)
print("og:title:", m.get("og:title", "")[:150])
print("og:url:", m.get("og:url", "")[:200])

# Estado embutido na página (lista de produtos costuma vir num JSON)
for nome in ("__PRELOADED_STATE__", "__NEXT_DATA__", "__INITIAL_STATE__", "melidata"):
    print(f"tem {nome}:", nome in pg)
blocos = re.findall(r"<script[^>]*>(.*?)</script>", pg, re.S)
print("scripts:", len(blocos), "| maiores:", sorted((len(b) for b in blocos), reverse=True)[:5])
for b in blocos:
    if len(b) > 20000:
        print("trecho do maior script:", re.sub(r"\s+", " ", b[:600]))
        break

# Links de produtos dentro da vitrine e seus parâmetros de rastreio
links = sorted(set(re.findall(r'https://(?:produto|www|click1|articulo)\.mercadoli[bv]re\.com\.br/[^"\'\s<>\\]{5,400}', pg)))
print("links de produto na vitrine:", len(links))
for l in links[:8]:
    mostrar_url("  produto", l.replace("&amp;", "&"))

# Pistas de rastreio de afiliado
for chave in ("matt_tool", "matt_word", "matt_source", "forceInApp", "ref=", "affiliate", "afiliad", "tracking_id"):
    achados = re.findall(r'.{0,60}' + re.escape(chave) + r'.{0,80}', pg)
    print(f"'{chave}' ({len(achados)}):", [re.sub(r"\s+", " ", a)[:140] for a in achados[:3]])

# Perfil da vitrine (ex.: /social/<apelido>) e se existe API de lista
perfis = sorted(set(re.findall(r'/social/[\w.-]+', pg)))
print("perfis /social/ citados:", perfis[:10])
apis = sorted(set(re.findall(r'https://[\w.-]*mercadoli[bv]re\.com[^"\'\s<>\\]*(?:social|affiliate|afiliad)[^"\'\s<>\\]*', pg)))
print("endereços de API/vitrine citados:", apis[:10])

# Abre o perfil sem parâmetros para ver se lista os produtos recomendados
if perfis:
    base = "https://www.mercadolivre.com.br" + perfis[0]
    r2 = requests.get(base, headers=H, timeout=30)
    print("\nPERFIL", base, "status", r2.status_code, "tamanho", len(r2.text))
    l2 = sorted(set(re.findall(r'https://(?:produto|www)\.mercadolivre\.com\.br/[^"\'\s<>\\]{5,300}', r2.text)))
    print("produtos no perfil:", len(l2))
    for l in l2[:5]:
        mostrar_url("  produto", l.replace("&amp;", "&"))
    print("títulos:", re.findall(r'"title"\s*:\s*"([^"]{10,90})"', r2.text)[:10])
    print("preços (Agora):", re.findall(r"Agora:\s*([\d.]+\s*reais(?:\s*com\s*\d+\s*centavos)?)", r2.text)[:10])
