/**
 * RK Gen AI Chatbot — JavaScript / Node integration example.
 *
 * Three ways to call the chatbot from any JS / TS project:
 *   1. fetch() against the REST API (zero deps, works in browser and Node 18+)
 *   2. EventSource / ReadableStream for SSE streaming
 *   3. WebSocket for bidirectional chat
 *
 * Run from the project root (requires a running backend on localhost:5000):
 *   node examples/javascript.js
 */

const API = process.env.API || "http://localhost:5000";

function section(title) {
  console.log(`\n── ${title} ──`);
}

// ── 1. fetch() — sync chat (zero deps) ─────────────────────────────
async function syncChat() {
  section("1. fetch() — sync chat");
  const r = await fetch(`${API}/api/integrate/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: "Tell me about InternOps" }),
  });
  const data = await r.json();
  console.log("provider:", data.provider);
  console.log("sources :", data.sources?.slice(0, 3));
  console.log("reply   :", data.reply.slice(0, 200) + "...");
}

// ── 2. SSE streaming via fetch + ReadableStream ────────────────────
async function streamChat() {
  section("2. SSE streaming (ReadableStream)");
  const r = await fetch(`${API}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: "What are his certifications?" }),
  });
  const reader = r.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  process.stdout.write("stream  : ");
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buf.indexOf("\n\n")) >= 0) {
      const raw = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const line = raw.split("\n").find((l) => l.startsWith("data: "));
      if (!line) continue;
      try {
        const ev = JSON.parse(line.slice(6));
        if (ev.type === "token") process.stdout.write(ev.content);
        if (ev.type === "done") console.log("\n          done, provider=" + ev.provider);
      } catch {}
    }
  }
}

// ── 3. WebSocket ───────────────────────────────────────────────────
async function wsChat() {
  section("3. WebSocket");
  const { WebSocket } = await import("ws").catch(() => ({ WebSocket: globalThis.WebSocket }));
  if (!WebSocket) {
    console.log("(WebSocket not available in this runtime — skipping)");
    return;
  }
  const ws = new WebSocket(API.replace(/^http/, "ws") + "/api/ws/chat");
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });
  ws.send(JSON.stringify({ message: "Hello from Node.js" }));
  let full = "";
  ws.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    if (ev.type === "token") full += ev.content;
    if (ev.type === "done") {
      console.log("ws reply:", full.slice(0, 200) + "...");
      ws.close();
    }
  };
  await new Promise((resolve) => ws.onclose = resolve);
}

(async () => {
  await syncChat();
  await streamChat();
  await wsChat();
})();
