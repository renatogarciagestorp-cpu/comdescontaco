"""Diagnóstico 2: o que a vitrine pública /social/<perfil> lista (componentes, itens, preços, links)."""
import json
import re
import sys

import requests

from .mercadolivre import UA

H = {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}


def estado(pg):
    m = re.search(r"_n\.ctx\.r=(\{.*?\});\s*(?:_n\.|</script>)", pg, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception as e:
        print("json falhou:", e)
        return None


def andar(o, achados, caminho=""):
    if isinstance(o, dict):
        if ("title" in o or "name" in o) and ("permalink" in o or "url" in o or "price" in o):
            achados.append((caminho, o))
        for k, v in o.items():
            andar(v, achados, caminho + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            andar(v, achados, caminho + f"[{i}]")


for url in sys.argv[1:]:
    r = requests.get(url, headers=H, timeout=30)
    print("\n=====", url, r.status_code, len(r.text))
    st = estado(r.text)
    if not st:
        print("sem estado; amostra:", re.sub(r"\s+", " ", r.text[:300]))
        continue
    comps = st.get("appProps", {}).get("pageProps", {}).get("data", {}).get("components", [])
    for c in comps:
        print("componente:", c.get("id"), "|", c.get("type"), "| chaves:", list(c.keys())[:8])
    achados = []
    andar(st, achados)
    print("itens encontrados:", len(achados))
    for cam, o in achados[:15]:
        resumo = {k: (str(v)[:120]) for k, v in o.items()
                  if k in ("id", "title", "name", "permalink", "url", "price", "original_price", "discount",
                           "price_info", "pictures", "thumbnail")}
        print(" ", cam[:80], json.dumps(resumo, ensure_ascii=False)[:500])
