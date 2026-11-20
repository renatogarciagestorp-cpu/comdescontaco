"""Diagnóstico (só API oficial de afiliados): o que a Shopee informa sobre preço e loja."""
import json
import sys

from .shopee import ShopeeAPI

api = ShopeeAPI()
kw = sys.argv[1] if len(sys.argv) > 1 else "mochila notebook"

Q = """query ($keyword: String) {
  productOfferV2(keyword: $keyword, sortType: 2, page: 1, limit: 5) {
    nodes { itemId shopId productName priceMin priceMax priceDiscountRate sales ratingStar
            shopName shopType }
  }
}"""
nodes = api._call(Q, {"keyword": kw})["productOfferV2"]["nodes"]
for n in nodes:
    print("PRODUTO:", json.dumps(n, ensure_ascii=False))

for n in nodes[:3]:
    sid = n["shopId"]
    for nome, q in (("literal", "{ shopOfferV2(shopId: %s, page: 1, limit: 1) { nodes { shopId shopName ratingStar shopType sellerCommCoveRatio } } }" % sid),
                    ("keyword", '{ shopOfferV2(keyword: "%s", page: 1, limit: 3) { nodes { shopId shopName ratingStar shopType } } }' % n["shopName"].replace('"', ""))):
        try:
            print(f"LOJA({nome}):", json.dumps(api._call(q, {}), ensure_ascii=False)[:400])
        except Exception as e:
            print(f"LOJA({nome}) erro:", str(e)[:200])
