"""Teste da conexão com o Instagram (rodado pelo botão no GitHub Actions).

1. Confere se o token funciona e mostra o @ da conta.
2. Inscreve a conta para receber avisos de comentários (webhook) no app.
Nunca imprime o token.
"""
import os
import sys

import requests

from .publishers import IG


def main():
    uid, token = os.environ.get("INSTAGRAM_USER_ID", "").strip(), os.environ.get("INSTAGRAM_TOKEN", "").strip()
    if not uid or not token:
        sys.exit("❌ Faltam os segredos INSTAGRAM_USER_ID e/ou INSTAGRAM_TOKEN no GitHub.")
    auth = {"Authorization": f"Bearer {token}"}
    ok = True

    r = requests.get(f"{IG}/{uid}", params={"fields": "id,username,followers_count,media_count"},
                     headers=auth, timeout=30)
    if r.ok:
        d = r.json()
        print(f"✅ Token OK. Conta: @{d.get('username')} | seguidores: {d.get('followers_count')} "
              f"| posts: {d.get('media_count')}")
    else:
        ok = False
        print(f"❌ Falha ao ler a conta ({r.status_code}): {r.text}")
        print("   Confira se INSTAGRAM_USER_ID é o ID da conta do Instagram (só números) e se o token foi colado inteiro.")

    r = requests.post(f"{IG}/{uid}/subscribed_apps", params={"subscribed_fields": "comments"},
                      headers=auth, timeout=30)
    if r.ok:
        print("✅ Conta inscrita para receber avisos de comentários (webhook 'comments').")
    else:
        ok = False
        print(f"⚠️ Não foi possível inscrever os comentários ({r.status_code}): {r.text}")

    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
