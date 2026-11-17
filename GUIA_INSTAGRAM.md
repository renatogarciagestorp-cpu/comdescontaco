# Guia: aprovar o app do Instagram na Meta

Objetivo: o bot publicar no feed sozinho e responder **"comente QUERO"** de **qualquer pessoa**.
Sem a aprovação (Advanced Access), o robô só responde contas cadastradas como testadoras do app.

Tempo total estimado: 1 a 3 semanas, a maior parte esperando a Meta responder.

---

## Etapa 1: preparar a conta do Instagram (5 min)
1. No app do Instagram: **Configurações → Tipo de conta e ferramentas → Mudar para conta profissional**. Escolha **Criador de conteúdo** ou **Empresa**, categoria "Compras e varejo".
2. Coloque na bio: o aviso de afiliado e o link do Telegram.
3. Publique de 3 a 6 posts. O revisor da Meta olha o perfil.

## Etapa 2: publicar as páginas obrigatórias (10 min)
A Meta exige uma **Política de Privacidade** e uma página de **Exclusão de dados**. Elas já estão prontas na pasta `docs/`.
1. O e-mail de contato das páginas já está preenchido.
2. No GitHub: **Settings → Pages → Branch: main / pasta /docs → Save**.
3. Em 1 a 2 minutos as páginas ficam no ar:
   - `https://SEU_USUARIO.github.io/SEU_REPOSITORIO/privacidade.html`
   - `https://SEU_USUARIO.github.io/SEU_REPOSITORIO/exclusao-dados.html`

## Etapa 3: criar a conta de desenvolvedor e o app (15 min)
1. Entre em **developers.facebook.com** com a sua conta do Facebook e clique em **Começar** para virar desenvolvedor. A Meta confirma o seu celular.
2. Clique em **Meus apps → Criar app**:
   - **Nome:** `comdescontaco`.
   - **Caso de uso:** "Gerenciar mensagens e conteúdo no Instagram".
   - **Portfólio empresarial:** crie um com o nome comdescontaco, se pedir.
3. No painel do app, abra **Configurações do app → Básico** e preencha:
   - **URL da Política de Privacidade:** o link de `privacidade.html`;
   - **URL de exclusão de dados do usuário:** o link de `exclusao-dados.html`;
   - **Ícone do app:** 1024×1024 com a logo;
   - **Categoria:** Compras;
   - **E-mail de contato.**
   - Clique em **Salvar alterações**.

## Etapa 4: ligar a API do Instagram e gerar o token (15 min)
1. No menu do app: **Instagram → Configuração da API com login do Instagram**.
2. Em **Gerar tokens de acesso**, clique em **Adicionar conta**, entre com o Instagram @comdescontaco e autorize tudo.
3. Copie:
   - o **ID do usuário do Instagram** → segredo `INSTAGRAM_USER_ID`;
   - o **Token** → segredo `INSTAGRAM_TOKEN`. Ele já é de longa duração e vale cerca de 60 dias.
4. Na mesma página, em **Configurar webhooks**:
   - **URL de callback:** o endereço do Cloudflare Worker (README, seção 5);
   - **Token de verificação:** o `VERIFY_TOKEN` que você inventou;
   - clique em **Verificar e salvar** e depois **assine o campo `comments`**.
5. Em **Configurações do app → Básico**, copie a **Chave secreta do app (App Secret)**. Ela é o `APP_SECRET` do Worker.

## Etapa 5: fazer chamadas de teste (obrigatório antes de pedir a análise)
A Meta só libera o pedido de análise depois de **pelo menos 1 chamada bem-sucedida** de cada permissão.
1. No GitHub, rode o bot (**Actions → Run workflow**). Isso usa `instagram_business_basic` e `instagram_business_content_publish`.
2. Com outra conta do Instagram **cadastrada como testadora**, comente "quero" num post do bot. Isso usa `instagram_business_manage_comments` e `instagram_business_manage_messages`.
   - Para cadastrar um testador: **Funções do app → Funções → Adicionar pessoas → Testador do Instagram**. Depois, aceite o convite no Instagram dessa conta em **Configurações → Apps e sites → Convites de testador**.
3. Confirme que a conta testadora recebeu o link no direct.
4. Aguarde até 24 h para o painel registrar as chamadas.

## Etapa 6: verificação da empresa (se a Meta pedir)
Em **Configurações do portfólio → Central de segurança → Verificação da empresa**, envie:
- **CNPJ** (um MEI resolve: é grátis e sai na hora pelo gov.br);
- comprovante com nome e endereço da empresa (cartão CNPJ ou conta de consumo);
- telefone, e-mail ou domínio para confirmação.

A Meta costuma pedir essa verificação para liberar o Advanced Access. Ter um **MEI** deixa tudo mais fácil e ainda serve para receber as comissões da Shopee.

## Etapa 7: gravar o vídeo (screencast)
Grave a tela, de 1 a 3 minutos, sem cortes, em inglês ou com legendas em inglês se possível. Mostre:
1. o login com o Instagram no painel do app (Etapa 4, "Adicionar conta");
2. um post sendo publicado pelo bot e aparecendo no perfil;
3. uma conta comentando **"quero"** no post;
4. a mensagem chegando no **direct** dessa conta com o link;
5. a resposta pública "Te mandei no direct!" aparecendo no comentário.

Dica: grave o celular espelhado no computador ou use a gravação de tela do celular. Deixe tudo bem legível.

## Etapa 8: enviar para análise
1. **Instagram → Configuração da API com login do Instagram → Concluir a análise do app**, depois **Continuar para análise do app**.
2. Peça **Acesso avançado** para:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
   - `instagram_business_manage_comments`
   - `instagram_business_manage_messages`
3. Para cada permissão, escreva o uso (texto pronto abaixo) e anexe o vídeo.
4. Em **Instruções para o revisor**, cole o texto pronto abaixo.
5. Clique em **Enviar para análise**. A resposta costuma chegar em 2 a 10 dias.
6. Depois da aprovação: **Publicar** o app, mudando a chave do topo de "Desenvolvimento" para **"Ao vivo / Publicado"**.

### Textos prontos (em inglês, que agiliza a análise)
**instagram_business_basic**
> Used to read our own Instagram professional account profile (ID and username) so our app can publish posts and reply to comments on our own account. We only access our own account (@comdescontaco).

**instagram_business_content_publish**
> Our app automatically publishes product deal images (price, discount, rating) to the feed of our own Instagram account @comdescontaco. Each post invites followers to comment a keyword to receive the product link.

**instagram_business_manage_comments**
> We receive comment webhooks on our own posts. When a user comments the keyword "quero" ("I want it" in Portuguese), we reply publicly on that comment saying the link was sent by direct message. We do not store comments.

**instagram_business_manage_messages**
> When a user comments the keyword "quero" on our post, we send that user ONE private reply (Private Replies API) containing the product link they asked for. Messages are only sent in response to the user's own comment request. We never send unsolicited messages and we do not store personal data.

**Instruções para o revisor**
> This app is used only by our own business account @comdescontaco. To test: 1) Open any recent post on instagram.com/comdescontaco. 2) Comment the word "quero". 3) Within a few seconds you will receive a direct message with the product link, and a public reply on your comment. The screencast shows the full flow, including Instagram Login in our app dashboard.

---

## Se for recusado
- Leia o motivo. Os mais comuns são vídeo sem o fluxo completo, política de privacidade incompleta e falta de verificação da empresa.
- Corrija e envie de novo. É normal precisar de 2 tentativas.

## Plano B enquanto espera
- O bot já publica no feed **sem** a aprovação, porque está publicando na **sua própria conta**.
- Durante a espera, a legenda pode mandar o público para o Telegram ("link na bio"). Se quiser, eu troco o texto "Comente QUERO" por "Link na bio" até a aprovação sair.
