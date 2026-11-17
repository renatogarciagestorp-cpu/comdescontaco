"""Teste do Telegram: publica a mensagem de boas-vindas no canal (botão no GitHub Actions)."""
import os
import sys
from pathlib import Path

import requests
import yaml

from .publishers import telegram_enviar_foto

RAIZ = Path(__file__).resolve().parent.parent


def main():
    faltando = [k for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID") if not os.environ.get(k, "").strip()]
    if faltando:
        sys.exit(f"❌ Faltam os segredos no GitHub: {', '.join(faltando)}")
    cfg = yaml.safe_load((RAIZ / "config.yaml").read_text())
    ch = cfg["canal"]

    token = os.environ["TELEGRAM_BOT_TOKEN"].strip()
    me = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=30).json()
    if not me.get("ok"):
        sys.exit(f"❌ Token do bot inválido: {me.get('description')}")
    print(f"✅ Bot encontrado: @{me['result']['username']}")

    legenda = "\n".join([
        "⚡ <b>Bem-vindo ao comdescontaco!</b>",
        "",
        "Aqui você recebe, todos os dias, as melhores ofertas, cupons e promoções relâmpago, "
        "com o link direto pra comprar. 🛒",
        "",
        "✅ Descontos de verdade (mínimo de 30%)",
        "⭐ Só produtos bem avaliados",
        "🔔 Ative as notificações pra não perder nada!",
        "",
        f"<i>{ch['aviso_afiliado']}</i>",
    ])
    insta = "https://instagram.com/" + ch["arroba_instagram"].lstrip("@")
    try:
        telegram_enviar_foto(RAIZ / "posts_iniciais" / "post_1.jpg", legenda, "📸 Siga no Instagram", insta)
    except RuntimeError as e:
        msg = str(e)
        dica = ""
        if "chat not found" in msg:
            dica = " → Confira o TELEGRAM_CHAT_ID: deve ser o @ do canal, ex.: @comdescontaco"
        elif "not enough rights" in msg or "administrator" in msg:
            dica = " → O bot precisa ser administrador do canal com permissão de publicar."
        sys.exit(f"❌ {msg}{dica}")
    print(f"✅ Mensagem de boas-vindas publicada em {os.environ['TELEGRAM_CHAT_ID']}")


if __name__ == "__main__":
    main()
