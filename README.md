# ⚡ descontaco.com: bot de ofertas automático

A cada 30 minutos, 24 horas por dia, de graça no GitHub, o bot:

1. busca produtos em promoção na **Shopee** pela API oficial de afiliados (o link já sai com a sua comissão);
2. filtra os melhores: desconto ≥ 30%, nota ≥ 4,6, ≥ 100 vendas e sem repetir produto por 7 dias;
3. limpa o título ("PROMOÇÃO ENVIO IMEDIATO [ORIGINAL]" vira um nome curto e legível);
4. gera a **arte 1080×1350 com neurodesign** (veja abaixo);
5. publica no **canal do Telegram** com o botão "COMPRAR AGORA". Entre 0h e 7h os posts saem **sem som**, para ninguém silenciar o canal;
6. a cada 6 h, publica uma **campanha oficial da Shopee** (cupons), com prazo real quando a Shopee informa;
7. manda as melhores ofertas do dia (até 8) para o **Instagram** com "Comente QUERO";
8. o **robô de comentários** responde quem comentar "quero" com o link no direct e uma resposta pública.

Tudo pode ser ajustado em `config.yaml`.

### Neurodesign aplicado nas artes
| Elemento | Efeito |
|---|---|
| Produto grande, com brilho atrás | O olho vai primeiro ao objeto de desejo (saliência) |
| Selo de % vermelho e girado | A quebra de padrão chama atenção; o número é lido em menos de meio segundo |
| "De" riscado em cima do "Por" | Ancoragem: o preço antigo vira referência |
| Centavos pequenos (47<sup>,90</sup>) | Efeito do dígito à esquerda: o preço parece menor |
| "Você economiza R$ X" em verde | Aversão à perda + sensação de ganho |
| Estrelas + "12,8 mil vendidos" | Prova social: reduz o medo de comprar errado |
| Um único botão amarelo com seta | Uma ação clara, sem distrações (efeito Von Restorff) |
| Ordem de leitura em Z | Marca → produto → preço → botão |

Só usamos gatilhos **verdadeiros**: nada de contador falso ou de "últimas unidades" inventado. Isso protege você do Código de Defesa do Consumidor e do bloqueio por parte da Shopee.

---

## Passo a passo (uma vez só)

### 1. Shopee: credenciais da API
No portal **affiliate.shopee.com.br**, abra o menu **Open API** e peça o acesso. Depois da aprovação, aparecem o **AppID** e o **Secret**.

### 2. Telegram: canal e bot
1. Crie um **Canal público** com o nome `descontaco.com` e o link `@descontaco` (se estiver em uso, escolha outro e troque em `config.yaml`).
2. No **@BotFather**, use `/newbot` e guarde o **token**.
3. Adicione o bot como **administrador** do canal.

### 3. GitHub: ligar o robô
1. Crie um repositório **público** e envie estes arquivos. Em repositório público, o GitHub Actions é ilimitado e os segredos continuam protegidos.
2. Em **Settings → Secrets and variables → Actions**, crie:

| Nome | Valor |
|---|---|
| `SHOPEE_APP_ID` | AppID da Shopee |
| `SHOPEE_SECRET` | Secret da Shopee |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ID` | `@descontaco` |

3. Em **Actions → descontaco bot → Run workflow**, rode para testar. Depois disso ele roda sozinho.

### 4. Instagram: publicação automática
1. Deixe o perfil como **conta Profissional** (Criador ou Empresa).
2. Em **developers.facebook.com**, crie um app do tipo "Empresa" e adicione o produto **Instagram → API com login do Instagram**.
3. Peça as permissões `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_comments` e `instagram_business_manage_messages`.
4. Gere o **token de longa duração** e anote o **ID do usuário do Instagram**.
5. No GitHub, crie os segredos `INSTAGRAM_USER_ID` e `INSTAGRAM_TOKEN`.
6. ⚠️ O token vence em cerca de 60 dias: renove antes disso.

### 5. Instagram: robô "comente QUERO" (Cloudflare Workers, grátis)
O GitHub não consegue "escutar" comentários. Por isso, o robô de comentários roda no Cloudflare Workers, que é gratuito até 100 mil eventos por dia.
1. Crie uma conta em **cloudflare.com**.
2. No seu computador, dentro da pasta `instagram-robo`:
   - edite `wrangler.toml`, trocando `SEU_USUARIO/SEU_REPOSITORIO` pelo seu repositório;
   - rode:
     ```bash
     npx wrangler login
     npx wrangler secret put INSTAGRAM_TOKEN      # mesmo token do passo 4
     npx wrangler secret put INSTAGRAM_USER_ID
     npx wrangler secret put APP_SECRET           # "Chave secreta do app" no painel da Meta
     npx wrangler secret put VERIFY_TOKEN         # invente uma senha qualquer
     npx wrangler deploy
     ```
   - o comando mostra um endereço como `https://descontaco-instagram.SEUNOME.workers.dev`.
3. No painel do app da Meta, em **Instagram → Webhooks**:
   - **URL de callback** = esse endereço;
   - **Token de verificação** = o `VERIFY_TOKEN` que você inventou;
   - assine o campo **comments**.
4. ⚠️ **Análise do app pela Meta:** enquanto o app está em "modo de desenvolvimento", o robô só responde contas cadastradas como testadoras. Para responder **qualquer pessoa**, envie o app para análise (App Review) pedindo as permissões de comentários e mensagens. Isso pode levar alguns dias e exige gravar um vídeo curto mostrando o funcionamento.

As palavras que disparam o robô são "quero", "eu quero", "link", "manda", "eu", 👍, 🔥 e 😍. Elas ficam em `instagram-robo/index.js`.

---

## Ver as artes sem publicar nada
```bash
pip install -r requirements.txt
python -m bot.main --demo     # cria exemplos em preview/
```

## Regras importantes
- **Avise que são links de afiliado** (CONAR). Coloque na descrição do canal: *"Links de afiliado: podemos ganhar comissão, sem custo extra pra você."* No Instagram, o bot já coloca `#publi`.
- Não use o nome nem o logo da Shopee como marca.
- O GitHub desativa agendamentos de repositórios parados há 60 dias. Os commits do bot evitam isso, mas, se o agendamento parar, é só reativar em **Actions**.
