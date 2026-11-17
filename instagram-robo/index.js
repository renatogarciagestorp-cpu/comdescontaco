// Robô de comentários do Instagram (Cloudflare Workers, plano gratuito).
// Quando alguém comenta uma palavra-chave (ex.: "quero") num post do bot:
//   1) envia o link do produto no direct da pessoa (Private Reply, API oficial da Meta);
//   2) responde o comentário publicamente ("te mandei no direct"), o que engaja o post.
// O link de cada post vem de data/instagram_links.json, que o bot grava no GitHub.

const API = "https://graph.facebook.com/v27.0"; // login unificado

const PALAVRAS = ["quero", "eu quero", "link", "manda", "me manda", "eu", "👍", "🔥", "😍"];

const RESPOSTAS_PUBLICAS = [
  "Te mandei no direct! 📩",
  "Enviado no seu direct! Corre que o preço pode subir ⚡",
  "Link no seu direct! 📲",
  "Mandei pra você no direct! 🛒",
];

function normalizar(t) {
  return (t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").trim();
}

export function temPalavraChave(texto) {
  const t = normalizar(texto);
  if (!t) return false;
  const palavras = t.split(/[^\p{L}\p{N}\p{Extended_Pictographic}]+/u).filter(Boolean);
  return PALAVRAS.some((p) => (p.includes(" ") ? t.includes(p) : palavras.includes(p) || t === p));
}

async function hmacValido(segredo, corpo, assinatura) {
  if (!assinatura?.startsWith("sha256=")) return false;
  const chave = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(segredo), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", chave, new TextEncoder().encode(corpo));
  const hex = [...new Uint8Array(mac)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return hex === assinatura.slice(7);
}

async function buscarLinks(env) {
  const r = await fetch(env.LINKS_URL, { cf: { cacheTtl: 60 } });
  return r.ok ? r.json() : {};
}

async function ig(env, caminho, corpo) {
  const r = await fetch(`${API}/${caminho}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${env.INSTAGRAM_TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  if (!r.ok) console.log(`erro ${caminho}: ${r.status} ${await r.text()}`);
  return r.ok;
}

export async function tratarComentario(env, v, contaId) {
  if (!v?.id || !temPalavraChave(v.text)) return "ignorado";
  if (v.from?.id === contaId || v.from?.id === env.INSTAGRAM_USER_ID) return "proprio";

  const links = await buscarLinks(env);
  const item = links[v.media?.id];
  const usuario = v.from?.username ? `@${v.from.username}` : "";
  const texto = item
    ? `Oi ${usuario}! 🔥 Aqui está o seu link:\n\n🛍️ ${item.nome}\n💰 ${item.preco}\n👉 ${item.link}\n\n` +
      `⚡ Ofertas como essa saem primeiro no nosso Telegram: ${env.TELEGRAM_LINK}`
    : `Oi ${usuario}! 🔥 Todas as nossas ofertas, com link, estão no Telegram: ${env.TELEGRAM_LINK}`;

  const ok = await ig(env, `${env.INSTAGRAM_USER_ID}/messages`, {
    recipient: { comment_id: v.id },
    message: { text: texto },
  });
  if (ok) {
    const resp = RESPOSTAS_PUBLICAS[Math.floor(Math.random() * RESPOSTAS_PUBLICAS.length)];
    await ig(env, `${v.id}/replies`, { message: resp });
    console.log(`direct enviado para ${usuario || v.from?.id} (comentário ${v.id})`);
  }
  return ok ? "enviado" : "falhou";
}

// ---------- Varredura a cada minuto (Cron Trigger) ----------
// A Meta só envia webhooks de comentários depois que o app é aprovado e publicado.
// Enquanto isso (e como reserva depois), o robô busca os comentários recentes sozinho.
// Não há risco de direct duplicado: a Meta aceita só UMA resposta privada por comentário.
const JANELA_MIN = 3; // olha comentários dos últimos 3 minutos

async function igGet(env, caminho, params) {
  const url = new URL(`${API}/${caminho}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const r = await fetch(url, { headers: { Authorization: `Bearer ${env.INSTAGRAM_TOKEN}` } });
  if (!r.ok) {
    console.log(`erro GET ${caminho}: ${r.status} ${await r.text()}`);
    return [];
  }
  return (await r.json()).data || [];
}

const quando = (ts) => Date.parse(String(ts).replace(/([+-]\d{2})(\d{2})$/, "$1:$2"));

export async function varrerComentarios(env, agora = Date.now()) {
  const limite = agora - JANELA_MIN * 60 * 1000;
  const posts = await igGet(env, `${env.INSTAGRAM_USER_ID}/media`, { fields: "id,timestamp", limit: "15" });
  const resultados = [];
  for (const post of posts) {
    if (quando(post.timestamp) < agora - 7 * 86400 * 1000) continue; // resposta privada só vale por 7 dias
    const comentarios = await igGet(env, `${post.id}/comments`, {
      fields: "id,text,timestamp,from{id,username}", limit: "50",
    });
    for (const c of comentarios) {
      if (quando(c.timestamp) < limite) continue;
      resultados.push(await tratarComentario(env, { ...c, media: { id: post.id } }, env.INSTAGRAM_USER_ID));
    }
  }
  return resultados;
}

export default {
  async scheduled(evento, env, ctx) {
    ctx.waitUntil(varrerComentarios(env));
  },

  async fetch(req, env, ctx) {
    const url = new URL(req.url);

    // Verificação do webhook (feita uma vez, no painel da Meta)
    if (req.method === "GET") {
      const ok = url.searchParams.get("hub.mode") === "subscribe" &&
        url.searchParams.get("hub.verify_token") === env.VERIFY_TOKEN;
      return ok ? new Response(url.searchParams.get("hub.challenge")) : new Response("ok");
    }

    if (req.method !== "POST") return new Response("método não permitido", { status: 405 });
    const corpo = await req.text();
    if (!(await hmacValido(env.APP_SECRET, corpo, req.headers.get("X-Hub-Signature-256")))) {
      return new Response("assinatura inválida", { status: 401 });
    }

    const dados = JSON.parse(corpo);
    const tarefas = [];
    for (const entrada of dados.entry || []) {
      for (const mudanca of entrada.changes || []) {
        if (mudanca.field === "comments") tarefas.push(tratarComentario(env, mudanca.value, entrada.id));
      }
    }
    ctx.waitUntil(Promise.all(tarefas)); // responde rápido à Meta e processa em seguida
    return new Response("EVENT_RECEIVED");
  },
};
