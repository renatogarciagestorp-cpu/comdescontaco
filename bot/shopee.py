"""Cliente da API de Afiliados da Shopee (GraphQL)."""
import hashlib
import json
import os
import time
from dataclasses import dataclass

import requests

ENDPOINT = "https://open-api.affiliate.shopee.com.br/graphql"

# sortType: 1 relevância, 2 mais vendidos, 3 maior preço, 4 menor preço, 5 maior comissão
PRODUCT_QUERY = """
query ($keyword: String, $page: Int, $limit: Int) {
  productOfferV2(keyword: $keyword, sortType: 2, page: $page, limit: $limit) {
    nodes {
      itemId productName imageUrl offerLink productLink
      priceMin priceMax priceDiscountRate sales ratingStar
      commissionRate shopName
    }
  }
}
"""

CAMPAIGN_QUERY = """
query ($page: Int, $limit: Int) {
  shopeeOfferV2(sortType: 1, page: $page, limit: $limit) {
    nodes {
      offerName imageUrl offerLink commissionRate periodStartTime periodEndTime
    }
  }
}
"""

SHORTLINK_MUTATION = """
mutation ($url: String!, $subIds: [String]) {
  generateShortLink(input: {originUrl: $url, subIds: $subIds}) { shortLink }
}
"""


@dataclass
class Produto:
    id: str
    nome: str
    imagem: str
    link: str
    link_original: str
    preco: float
    preco_antigo: float
    desconto: int
    vendas: int
    nota: float
    comissao: float
    loja: str
    plataforma: str = "Shopee"


@dataclass
class Campanha:
    id: str
    nome: str
    imagem: str
    link: str
    fim: int


class ShopeeAPI:
    def __init__(self, app_id: str | None = None, secret: str | None = None):
        self.app_id = app_id or os.environ["SHOPEE_APP_ID"]
        self.secret = secret or os.environ["SHOPEE_SECRET"]

    def _call(self, query: str, variables: dict) -> dict:
        body = json.dumps({"query": query, "variables": variables}, separators=(",", ":"))
        ts = str(int(time.time()))
        sig = hashlib.sha256(f"{self.app_id}{ts}{body}{self.secret}".encode()).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={ts}, Signature={sig}",
        }
        r = requests.post(ENDPOINT, data=body.encode(), headers=headers, timeout=30)
        r.raise_for_status()
        payload = r.json()
        if payload.get("errors"):
            raise RuntimeError(f"Shopee API: {payload['errors']}")
        return payload["data"]

    def buscar_produtos(self, palavra: str, limite: int = 30) -> list[Produto]:
        data = self._call(PRODUCT_QUERY, {"keyword": palavra, "page": 1, "limit": limite})
        produtos = []
        for n in data["productOfferV2"]["nodes"]:
            preco = float(n.get("priceMin") or 0)
            desconto = int(n.get("priceDiscountRate") or 0)
            if preco <= 0:
                continue
            antigo = round(preco / (1 - desconto / 100), 2) if 0 < desconto < 100 else preco
            produtos.append(Produto(
                id=str(n["itemId"]),
                nome=n["productName"].strip(),
                imagem=n["imageUrl"],
                link=n["offerLink"],
                link_original=n["productLink"],
                preco=preco,
                preco_antigo=antigo,
                desconto=desconto,
                vendas=int(n.get("sales") or 0),
                nota=float(n.get("ratingStar") or 0),
                comissao=float(n.get("commissionRate") or 0),
                loja=n.get("shopName") or "",
            ))
        return produtos

    def buscar_campanhas(self, limite: int = 20) -> list[Campanha]:
        data = self._call(CAMPAIGN_QUERY, {"page": 1, "limit": limite})
        agora = time.time()
        out = []
        for n in data["shopeeOfferV2"]["nodes"]:
            fim = int(n.get("periodEndTime") or 0)
            if fim and fim < agora:
                continue
            out.append(Campanha(id=n["offerLink"], nome=n["offerName"], imagem=n["imageUrl"],
                                link=n["offerLink"], fim=fim))
        return out

    def link_rastreado(self, url: str, canal: str) -> str:
        """Gera link curto com subId (ex.: 'telegram') para saber de onde veio a venda."""
        try:
            data = self._call(SHORTLINK_MUTATION, {"url": url, "subIds": [canal]})
            return data["generateShortLink"]["shortLink"]
        except Exception as e:  # o offerLink já é de afiliado; o subId é só um extra
            print(f"[aviso] shortlink falhou, usando offerLink: {e}")
            return ""
