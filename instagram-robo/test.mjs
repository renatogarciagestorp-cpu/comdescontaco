// Teste local: node test.mjs
import worker, { temPalavraChave } from "./index.js";
import assert from "node:assert";
import crypto from "node:crypto";

for (const t of ["Quero", "QUERO!!", "eu quero muito", "quero 😍", "Manda o link", "🔥"]) assert(temPalavraChave(t), t);
for (const t of ["não sei", "querosene", "lindo", ""]) assert(!temPalavraChave(t), t);

const env = { INSTAGRAM_TOKEN: "tok", INSTAGRAM_USER_ID: "999", APP_SECRET: "seg", VERIFY_TOKEN: "vt",
  LINKS_URL: "https://raw/links.json", TELEGRAM_LINK: "https://t.me/comdescontaco" };
const chamadas = [];
globalThis.fetch = async (url, opt = {}) => {
  if (url === env.LINKS_URL) return new Response(JSON.stringify({ M1: { link: "https://s.shopee.com.br/abc", nome: "Fone TWS", preco: "R$ 47,90" } }));
  chamadas.push({ url, body: JSON.parse(opt.body) });
  return new Response("{}");
};
const ctx = { waitUntil: (p) => (ctx.p = p) };

// verificação do webhook
let r = await worker.fetch(new Request("https://w/?hub.mode=subscribe&hub.verify_token=vt&hub.challenge=123"), env, ctx);
assert.equal(await r.text(), "123");

const evento = (texto, de = "555") => JSON.stringify({ object: "instagram", entry: [{ id: "999", changes: [{ field: "comments",
  value: { id: "C1", text: texto, from: { id: de, username: "maria" }, media: { id: "M1" } } }] }] });
const assinar = (b) => "sha256=" + crypto.createHmac("sha256", "seg").update(b).digest("hex");

// assinatura errada
r = await worker.fetch(new Request("https://w/", { method: "POST", body: evento("quero"), headers: { "X-Hub-Signature-256": "sha256=00" } }), env, ctx);
assert.equal(r.status, 401);

// comentário "Quero!" → direct + resposta pública
let b = evento("Quero!");
r = await worker.fetch(new Request("https://w/", { method: "POST", body: b, headers: { "X-Hub-Signature-256": assinar(b) } }), env, ctx);
await ctx.p;
assert.equal(chamadas.length, 2);
assert.match(chamadas[0].url, /999\/messages$/);
assert.equal(chamadas[0].body.recipient.comment_id, "C1");
assert.match(chamadas[0].body.message.text, /s\.shopee\.com\.br\/abc/);
assert.match(chamadas[1].url, /C1\/replies$/);
console.log(chamadas[0].body.message.text, "\n---\n", chamadas[1].body.message);

// a própria conta comentando não dispara (evita loop)
chamadas.length = 0; b = evento("quero", "999");
await worker.fetch(new Request("https://w/", { method: "POST", body: b, headers: { "X-Hub-Signature-256": assinar(b) } }), env, ctx);
await ctx.p; assert.equal(chamadas.length, 0);
console.log("\nTODOS OS TESTES PASSARAM");

// ---- varredura por Cron ----
import { varrerComentarios } from "./index.js";
const agora = Date.parse("2026-11-17T16:40:00Z");
chamadas.length = 0;
const gets = [];
globalThis.fetch = async (url, opt = {}) => {
  const u = String(url);
  if (u === env.LINKS_URL) return new Response("{}");
  if (!opt.method || opt.method === "GET") {
    gets.push(u);
    if (u.includes("/999/media")) return new Response(JSON.stringify({ data: [
      { id: "P1", timestamp: "2026-11-17T10:00:00+0000" },
      { id: "VELHO", timestamp: "2026-10-01T10:00:00+0000" } ] }));
    if (u.includes("/P1/comments")) return new Response(JSON.stringify({ data: [
      { id: "N1", text: "Quero!", timestamp: "2026-11-17T16:39:10+0000", from: { id: "555", username: "maria" } },
      { id: "N2", text: "lindo", timestamp: "2026-11-17T16:39:20+0000", from: { id: "556", username: "joao" } },
      { id: "A1", text: "quero", timestamp: "2026-11-17T16:20:00+0000", from: { id: "557", username: "ana" } } ] }));
    return new Response("{}");
  }
  chamadas.push({ url: u, body: JSON.parse(opt.body) });
  return new Response("{}");
};
const res = await varrerComentarios(env, agora);
assert.deepEqual(res, ["enviado", "ignorado"]);            // A1 é antigo, N2 não tem palavra-chave
assert(!gets.some((g) => g.includes("VELHO")));            // post com mais de 7 dias é pulado
assert.equal(chamadas[0].body.recipient.comment_id, "N1");
assert.match(chamadas[0].body.message.text, /t\.me\/comdescontaco/); // sem link de produto → Telegram
console.log("VARREDURA OK");

// ---- agenda do "relógio" ----
import { agenda } from "./index.js";
const at = (h, m) => agenda(new Date(Date.UTC(2026, 10, 20, h, m)));
assert.deepEqual(at(10, 0), ["bot.yml"]);
assert.deepEqual(at(10, 5), ["mercadolivre.yml"]);
assert.deepEqual(at(22, 7), ["conteudo-instagram.yml"]);
assert.deepEqual(at(10, 13), []);
console.log("AGENDA OK");
