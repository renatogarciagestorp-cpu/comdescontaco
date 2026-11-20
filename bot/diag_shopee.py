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

QS = """query ($shopId: Int64) {
  shopOfferV2(shopId: $shopId, page: 1, limit: 1) {
    nodes { shopId shopName ratingStar shopType }
  }
}"""
for n in nodes[:3]:
    try:
        print("LOJA:", json.dumps(api._call(QS, {"shopId": int(n["shopId"])}), ensure_ascii=False))
    except Exception as e:
        print("LOJA erro:", str(e)[:300])
