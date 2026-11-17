# Guia: credenciais da API de Afiliados da Shopee (AppID e Secret)

## Antes de começar
- Tenha o cadastro no **Programa de Afiliados da Shopee** aprovado e ativo.
- Crie antes o canal do Telegram e o perfil do Instagram e faça alguns posts manuais. A Shopee pede os links dos seus canais, e canais com conteúdo são aprovados mais facilmente.

## Passo a passo
1. No computador, entre em **affiliate.shopee.com.br** e faça login com a sua conta de afiliado.
2. Abra **affiliate.shopee.com.br/open_api**. O mesmo caminho pode aparecer no menu como **"Open API"** ou **"Ferramentas → Open API"**.
3. Clique para **solicitar acesso** e preencha o formulário:
   - **Já é afiliado?** Sim.
   - **Nome e e-mail:** os mesmos da conta de afiliado.
   - **Canais de divulgação:** `https://t.me/comdescontaco` e `https://instagram.com/comdescontaco`.
   - **Como vai usar a API:** algo como *"Automação de um canal de ofertas no Telegram e no Instagram: buscar produtos em promoção (productOfferV2), gerar links de afiliado (generateShortLink) e divulgar campanhas oficiais da Shopee (shopeeOfferV2)."*
   - **Volume esperado:** ~50 posts por dia.
4. Envie e aguarde. A resposta chega por **e-mail** e costuma levar de alguns dias a algumas semanas.
5. Depois da aprovação, volte a **affiliate.shopee.com.br/open_api**. Lá aparecem o **AppID** (um número) e o **Secret** (um código longo).
   - ⚠️ O Secret é uma senha. **Não envie para ninguém**, nem para mim no chat. Ele vai direto para os Secrets do GitHub.
6. No repositório do GitHub, vá em **Settings → Secrets and variables → Actions → New repository secret** e crie:
   - `SHOPEE_APP_ID` com o AppID;
   - `SHOPEE_SECRET` com o Secret.

## Se demorar
- Confira a caixa de spam.
- Depois de 2 semanas sem resposta, abra um chamado no **suporte de afiliados** da Shopee pedindo a "liberação do acesso à Open API de afiliados".
