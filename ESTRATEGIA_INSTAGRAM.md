# Estratégia de Instagram: @comdescontaco

**Objetivo:** ganhar seguidores qualificados (gente que gosta de economizar) e levar essas pessoas ao Telegram, onde as compras acontecem.
**Funil:** Instagram (alcance) → "Comente QUERO" / link na bio → Telegram (ofertas 24h) → compra (comissão).

---

## 1. Perfil (10 min, fazer hoje no app)

O Instagram não permite alterar o perfil pela API, então estes passos são manuais.

| Item | O que colocar | Por quê |
|---|---|---|
| **Nome** (o campo "Nome", não o @) | `comdescontaco • Ofertas e Cupons` | O campo Nome entra na **busca**: quem pesquisar "ofertas" ou "cupons" encontra você |
| **Bio** | ver abaixo | Explica em 3 segundos o que a pessoa ganha |
| **Link** | `t.me/comdescontaco` | Leva direto ao canal |
| **Categoria** | Compras e varejo (ou "Site de compras") | Aparece abaixo do nome |
| **Foto** | `posts_iniciais/foto_perfil.jpg` (o raio) | Reconhecível mesmo pequeno |
| **Destaques** | capas em `conteudo/destaques/` | Organizam o perfil e convertem quem acabou de chegar |

**Bio (copie e cole):**
```
⚡ Ofertas e cupons de verdade, todo dia
💬 Comente QUERO e receba o link no direct
🔔 Relâmpagos 24h no Telegram 👇
Links de afiliado
```

**Destaques (crie a partir dos Stories que o robô publica):**
- **COMO FUNCIONA:** o post 2 ("Receba o link em 3 passos")
- **TELEGRAM:** o post 3 e o "Por que entrar no nosso canal"
- **DICAS:** os posts de cupom, frete, avaliações e golpes
- **BLACK FRIDAY:** as contagens regressivas e o checklist
- **OFERTAS** e **CUPONS:** os Stories das ofertas, quando a Shopee liberar

Para trocar a capa: segure o destaque → Editar destaque → Editar capa → escolha a imagem em `conteudo/destaques/`.

---

## 2. O que o robô já faz sozinho

| Conteúdo | Frequência | Formato |
|---|---|---|
| Post de conteúdo (dicas, Black Friday, engajamento) | 1 por dia, às 19h | **Reel animado** (aparece também no feed) + **Story** |
| Ofertas da Shopee (quando a API for liberada) | até 8 por dia, só as melhores | as 2 melhores viram **Reel**, as demais saem como **imagem**; todas ganham **Story** |
| Resposta "comente QUERO" | na hora | Direct + resposta no comentário |

**Tudo é gerado e publicado pelo robô.** Se um Reel falhar, ele publica a imagem no lugar.
O que a API da Meta não permite automatizar nos Stories: enquete, caixa de perguntas, link e música. Esses adesivos são opcionais, para quando você quiser postar pelo app.

O calendário está em `conteudo/banco.yaml`. Para adicionar posts, siga o mesmo formato. Quando o banco acabar, eu escrevo mais.

**Mistura ideal:** cerca de 70% ofertas e 30% conteúdo útil ou de engajamento. Um perfil só de ofertas vira "catálogo" e para de crescer; o conteúdo útil é o que gera **compartilhamentos e salvamentos**.

---

## 3. Calendário da Black Friday (27/11)

| Data | Post automático | O que você faz |
|---|---|---|
| 18/11 | 5 sinais de desconto falso | Compartilhar nos Stories pessoais |
| 19/11 | ⏳ Contagem: faltam 8 dias | Story com enquete "Vai comprar na Black?" |
| 20/11 | O que você quer achar em promoção? | **Responder todos os comentários** |
| 21/11 | Cupom em 4 passos (Reel automático) | Responder comentários |
| 22/11 | Marque o amigo que paga caro | Responder comentários |
| 23/11 | Não caia em golpe | Enviar em grupos de família no WhatsApp |
| 24/11 | ⏳ Contagem: faltam 3 dias (Reel automático) | Compartilhar nos seus Stories |
| 25/11 | Checklist Black Friday | Story com caixa de perguntas |
| 26/11 | ⏳ É amanhã! | Story: "Ative as notificações do Telegram" |
| **27/11** | **Por que entrar no Telegram** + ofertas | Stories ao longo do dia mostrando as ofertas |
| 28/11 em diante | Avaliações, frete, dezembro, Natal | Responder comentários |

---

## 4. Reels (o que mais traz seguidores novos)

Os Reels são **gerados e publicados automaticamente** pelo robô: conteúdo diário e as 2 melhores ofertas do dia.
Para ter trilha sonora, coloque músicas livres de direitos em `assets/audio/`.

Se um dia quiser gravar um Reel extra (opcional), estes roteiros funcionam bem:

- **Roteiro A, "Eu paguei X, você pode pagar Y":** tela do produto com o preço cheio → corte → o mesmo produto com desconto → texto "comente QUERO".
- **Roteiro B, "3 achados abaixo de R$ 50":** gravação de tela rolando 3 produtos → texto grande com o preço → "link no direct: comente QUERO".
- **Roteiro C, "Desconto falso?":** mostra um "de/por" suspeito → explica em 1 frase → "aqui só entra oferta verificada".
- **Gancho nos 2 primeiros segundos:** "Não compre nada na Black Friday antes de ver isso".

---

## 5. Rotina diária (10 minutos; todo o resto é automático)

1. **Responder todos os comentários** na primeira hora depois do post das 19h. O algoritmo premia conversa. Os "quero" o robô responde sozinho.
2. **Comentar em 10 posts** de perfis grandes de ofertas, cupons ou economia. Comentários úteis, nunca "sigam-me". Quem lê vê o seu perfil.
3. Compartilhar o Reel do dia nos seus Stories pessoais e em grupos de WhatsApp.
4. (Opcional) Um Story com enquete pelo app, por exemplo "Vai comprar na Black Friday?", para aumentar o alcance.

---

## 6. Táticas de crescimento

- **"Comente QUERO":** cada comentário aumenta o alcance do post, e o robô já entrega o link.
- **Collab:** convide microinfluenciadores de economia ou achadinhos (5 a 50 mil seguidores) para posts em **Colaboração**. O post aparece nos dois perfis. Ofereça uma parte da comissão.
- **Telegram ↔ Instagram:** divulgue o Instagram no Telegram e vice-versa.
- **Indique e ganhe (no futuro):** "Marque 2 amigos e concorra...". ⚠️ **Sorteios no Brasil** podem exigir autorização do governo (Lei 5.768/71). Prefira "desafios" sem sorteio ou consulte as regras antes.

**Nunca faça:** comprar seguidores, usar robôs de seguir e deixar de seguir, ou responder DMs em massa. O Instagram detecta e **derruba o alcance ou bloqueia a conta**, e isso também prejudicaria a análise do app na Meta.

---

## 7. Métricas (toda segunda-feira, em Insights)

| Métrica | Meta inicial |
|---|---|
| Contas alcançadas (7 dias) | crescer 20% por semana |
| Seguidores novos | 50+ por semana no 1º mês |
| Salvamentos + compartilhamentos | repetir os temas dos posts campeões |
| Cliques no link da bio | aumentar a cada semana |
| Membros no Telegram | acompanhar junto com os seguidores |

Me mande um print dos Insights toda semana. Eu analiso, ajusto o calendário e escrevo novos posts com base no que funcionou.
