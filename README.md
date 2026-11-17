# ⚡ Garimpo Relâmpago: bot de ofertas automático

A cada 30 minutos, de graça, no GitHub, o bot:

1. busca produtos em promoção na **Shopee** pela API oficial de afiliados (o link já sai com a sua comissão);
2. filtra os melhores: desconto ≥ 30%, nota ≥ 4,6, ≥ 100 vendas e sem repetir produto por 7 dias;
3. gera a **arte 1080×1080** com foto, preço "de/por" e selo de % OFF;
4. publica no **canal do Telegram** com botão "Comprar agora";
5. a cada 6 h, publica uma **campanha oficial da Shopee** (cupons e ofertas relâmpago);
6. manda as melhores ofertas do dia (até 6) para o **feed do Instagram**, com chamada para o Telegram.

Não posta entre 0h e 7h. Tudo isso pode ser mudado em `config.yaml`.

---

## Passo a passo (uma vez só)

### 1. Shopee: pegar as credenciais da API
1. Entre em **affiliate.shopee.com.br** → menu **Open API** (ou "Ferramentas → API").
2. Peça o acesso, se ainda não tiver. Depois de aprovado, aparecem o **AppID** e o **Secret**.

### 2. Telegram: criar canal e bot
1. No Telegram, crie um **Canal público** chamado `Garimpo Relâmpago`, com o link `@garimporelampago` (se o @ estiver em uso, escolha outro e atualize `config.yaml`).
2. Abra o **@BotFather** → `/newbot` → guarde o **token**.
3. Adicione o bot como **administrador** do canal, com permissão de postar.
4. O **chat id** é o próprio @ do canal: `@garimporelampago`.

### 3. GitHub: subir o projeto e ligar o robô
1. Crie um repositório **público** (Actions é ilimitado em repositórios públicos; os segredos continuam protegidos) e envie estes arquivos.
2. Vá em **Settings → Secrets and variables → Actions → New repository secret** e crie:

| Nome | Valor |
|---|---|
| `SHOPEE_APP_ID` | AppID da Shopee |
| `SHOPEE_SECRET` | Secret da Shopee |
| `TELEGRAM_BOT_TOKEN` | token do BotFather |
| `TELEGRAM_CHAT_ID` | `@garimporelampago` |

3. Na aba **Actions**, clique em **Garimpo Bot → Run workflow** para testar na hora. A partir daí ele roda sozinho.

### 4. Instagram (opcional, pode ser feito depois)
1. Transforme o perfil em **conta Profissional** (Criador ou Empresa).
2. Crie um app em **developers.facebook.com** com o produto "Instagram API with Instagram Login" e a permissão `instagram_business_content_publish`.
3. Gere um **token de longa duração** e pegue o **ID do usuário do Instagram**.
4. Crie os segredos `INSTAGRAM_USER_ID` e `INSTAGRAM_TOKEN`.
5. ⚠️ O token vence em cerca de 60 dias. Renove e atualize o segredo antes disso.

Sem esses segredos, o bot simplesmente pula o Instagram.

---

## Testar o visual no seu computador
```bash
pip install -r requirements.txt
python -m bot.main --demo     # cria exemplos em preview/ sem publicar nada
```

## Ajustes comuns (`config.yaml`)
- `palavras_chave`: o que o bot procura (nicho geral: dá para trocar à vontade).
- `filtros`: desconto mínimo, nota, vendas e preço máximo.
- `posts_por_execucao` e o `cron` em `.github/workflows/bot.yml`: frequência dos posts.
- `cores` e `canal`: identidade visual.

## Regras importantes
- **Avise que são links de afiliado** (CONAR). Coloque na descrição do canal: *"Links de afiliado: podemos ganhar comissão, sem custo extra pra você."* No Instagram, o bot já coloca `#publi`.
- Não use o nome nem o logo da Shopee como marca do canal.
- O GitHub **desativa agendamentos de repositórios sem atividade por 60 dias**. Como o bot faz commits a cada execução, isso não deve acontecer, mas se parar, é só reativar em **Actions**.
