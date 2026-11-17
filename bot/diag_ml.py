"""Diagnóstico: abre um link do Mercado Livre e mostra onde estão nome, foto e preço na página."""
import re
import sys

import requests

from .mercadolivre import UA, _jsonld, _metas, extrair

url = sys.argv[1]
r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}, timeout=30)
pg = r.text
print("status:", r.status_code, "| final:", r.url, "| tamanho:", len(pg))
print("histórico:", [h.url for h in r.history])
m = _metas(pg)
for k in ("og:title", "og:image", "og:url", "price", "product:price:amount", "twitter:data1"):
    print(f"meta {k}:", m.get(k, "")[:150])
print("jsonld:", [str(p)[:400] for p in _jsonld(pg)])
for nome, rx in [("fraction", r'andes-money-amount__fraction[^>]*>([\d.]+)<'),
                 ("aria", r'aria-label="([^"]*(?:reais|Antes|Agora)[^"]*)"'),
                 ("price_json", r'"price"\s*:\s*\{?[^,}]{0,80}'),
                 ("original_price", r'"original_price"\s*:\s*[^,]{0,30}'),
                 ("amount", r'"amount"\s*:\s*[\d.]+'),
                 ("off", r'\d{1,2}%\s*OFF'),
                 ("MLB", r'MLB-?\d{6,}'),
                 ("links_produto", r'https://(?:produto|www)\.mercadolivre\.com\.br/[^"\s]{10,120}')]:
    achados = re.findall(rx, pg)
    print(f"{nome} ({len(achados)}):", achados[:6])

print("RESULTADO DO ROBÔ:", extrair(pg, r.url))
