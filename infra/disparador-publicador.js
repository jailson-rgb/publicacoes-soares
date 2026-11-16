// DISPARADOR DOS PUBLICADORES – GRUPO JASA (Advocacia Soares + Justo Acordo)
// Cloudflare Worker com Cron Trigger "4,19,34,49 * * * *" (a cada 15 min, fora do minuto 0).
// A cada execução:
//   1. dispara o workflow publicar.yml dos dois repositórios (workflow_dispatch);
//   2. confere quando cada publicador terminou a última rodada; se passar de 45 min,
//      abre uma issue "PUBLICADOR PARADO" no repositório (o GitHub manda e-mail ao Jailson);
//      quando volta a rodar, fecha a issue sozinho.
// Segredo necessário (Settings > Variables and Secrets do Worker): GH_TOKEN
//   token fine-grained do GitHub, só para os 2 repositórios, com permissões
//   Actions: Read and write e Issues: Read and write. Colado pelo Jailson, nunca no chat.
// O cron do próprio GitHub continua como reserva; a trava "concurrency" dos workflows
// impede duas rodadas ao mesmo tempo e o publicador não republica o que já saiu.

const REPOS = ["jailson-rgb/publicacoes-soares", "jailson-rgb/publicacoes-justoacordo"];
const WORKFLOW = "publicar.yml";
const LIMITE_MIN = 45;
const TITULO_ALARME = "PUBLICADOR PARADO (aviso automático do disparador)";

async function gh(env, path, opts = {}) {
  return fetch("https://api.github.com" + path, {
    ...opts,
    headers: {
      "Authorization": "Bearer " + env.GH_TOKEN,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "disparador-publicador-jasa",
      ...(opts.body ? { "Content-Type": "application/json" } : {}),
    },
  });
}

async function cuidarDoRepo(env, repo) {
  const problemas = [];

  // 1. Disparar
  const d = await gh(env, `/repos/${repo}/actions/workflows/${WORKFLOW}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: "main" }),
  });
  if (d.status !== 204) problemas.push(`disparo falhou (HTTP ${d.status})`);

  // 2. Última rodada concluída
  const r = await gh(env, `/repos/${repo}/actions/workflows/${WORKFLOW}/runs?status=completed&per_page=1`);
  if (r.ok) {
    const j = await r.json();
    const ultima = j.workflow_runs && j.workflow_runs[0];
    if (ultima) {
      const min = (Date.now() - Date.parse(ultima.updated_at)) / 60000;
      if (min > LIMITE_MIN) problemas.push(`última rodada concluída há ${Math.round(min)} min`);
    }
  } else {
    problemas.push(`não consegui ler as rodadas (HTTP ${r.status})`);
  }

  // 3. Alarme por issue (abre uma só; fecha quando normaliza)
  const busca = await gh(env, `/repos/${repo}/issues?state=open&per_page=50`);
  const abertas = busca.ok ? await busca.json() : [];
  const alarme = abertas.find((i) => i.title === TITULO_ALARME && !i.pull_request);
  const agora = new Date().toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });

  if (problemas.length && !alarme && busca.ok) {
    await gh(env, `/repos/${repo}/issues`, {
      method: "POST",
      body: JSON.stringify({
        title: TITULO_ALARME,
        body: `Em ${agora}: ${problemas.join("; ")}.\n\nConferir a aba Actions do repositório e o token GH_TOKEN do Worker na Cloudflare. Esta issue fecha sozinha quando o publicador voltar a rodar.`,
      }),
    });
  } else if (!problemas.length && alarme) {
    await gh(env, `/repos/${repo}/issues/${alarme.number}/comments`, {
      method: "POST",
      body: JSON.stringify({ body: `Normalizado em ${agora}.` }),
    });
    await gh(env, `/repos/${repo}/issues/${alarme.number}`, {
      method: "PATCH",
      body: JSON.stringify({ state: "closed" }),
    });
  }
  return `${repo}: ${problemas.length ? problemas.join("; ") : "ok"}`;
}

async function rodar(env) {
  const res = await Promise.all(REPOS.map((repo) => cuidarDoRepo(env, repo).catch((e) => `${repo}: erro ${e}`)));
  console.log(res.join(" | "));
  return res;
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(rodar(env));
  },
  // Abrir a URL do Worker só mostra que ele está no ar (não dispara nada).
  async fetch() {
    return new Response("Disparador dos publicadores GRUPO JASA: ativo (roda a cada 15 min).", {
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  },
};
