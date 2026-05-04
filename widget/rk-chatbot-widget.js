/*!
 * RK Gen AI Chatbot — Embed Widget
 * Drop into any website with a single <script> tag.
 *
 * Usage:
 *   <script src="/widget/rk-chatbot-widget.js"
 *           data-api-url="https://chatbot.example.com"
 *           data-title="Ask about Rajat"
 *           data-theme="dark"></script>
 *
 * Config (all optional):
 *   data-api-url    Backend base URL (default: http://localhost:5000)
 *   data-title      Header title             (default: "Ask me anything")
 *   data-subtitle   Header subtitle          (default: "AI Assistant")
 *   data-theme      "light" | "dark"         (default: "light")
 *   data-position   "bottom-right" | "bottom-left"  (default: "bottom-right")
 *   data-accent     Hex accent color         (default: #ff6d34)
 *   data-greeting   Initial bot message      (default: "Hi! How can I help?")
 */
(function () {
  if (window.__RK_CHATBOT_WIDGET_LOADED__) return;
  window.__RK_CHATBOT_WIDGET_LOADED__ = true;

  var scripts = document.getElementsByTagName("script");
  var script = scripts[scripts.length - 1];
  var cfg = {
    apiUrl: script.getAttribute("data-api-url") || "http://localhost:5000",
    title: script.getAttribute("data-title") || "Ask me anything",
    subtitle: script.getAttribute("data-subtitle") || "AI Assistant",
    theme: script.getAttribute("data-theme") || "light",
    position: script.getAttribute("data-position") || "bottom-right",
    accent: script.getAttribute("data-accent") || "#ff6d34",
    greeting: script.getAttribute("data-greeting") || "Hi! How can I help?",
  };

  var isDark = cfg.theme === "dark";
  var colors = isDark
    ? { bg: "#0f172a", panel: "#1e293b", text: "#f1f5f9", muted: "#94a3b8", border: "#334155", input: "#0f172a" }
    : { bg: "#ffffff", panel: "#ffffff", text: "#0f172a", muted: "#64748b", border: "#e2e8f0", input: "#f8fafc" };

  var css = "" +
    ".rk-chat-fab{position:fixed;" + (cfg.position === "bottom-left" ? "left:24px;" : "right:24px;") + "bottom:24px;width:60px;height:60px;border-radius:50%;background:" + cfg.accent + ";color:#fff;border:none;cursor:pointer;box-shadow:0 10px 30px rgba(0,0,0,.25);z-index:99998;display:flex;align-items:center;justify-content:center;transition:transform .2s;font-size:24px;}" +
    ".rk-chat-fab:hover{transform:scale(1.05);}" +
    ".rk-chat-panel{position:fixed;" + (cfg.position === "bottom-left" ? "left:24px;" : "right:24px;") + "bottom:96px;width:min(380px,calc(100vw - 32px));height:min(560px,calc(100vh - 140px));background:" + colors.panel + ";color:" + colors.text + ";border:1px solid " + colors.border + ";border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.2);z-index:99999;display:none;flex-direction:column;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;}" +
    ".rk-chat-panel.open{display:flex;}" +
    ".rk-chat-header{padding:14px 16px;background:" + cfg.accent + ";color:#fff;display:flex;align-items:center;gap:10px;flex-shrink:0;}" +
    ".rk-chat-header .dot{width:8px;height:8px;border-radius:50%;background:#00d4a0;box-shadow:0 0 0 3px rgba(0,212,160,.25);animation:rkpulse 2s infinite;}" +
    "@keyframes rkpulse{0%,100%{opacity:1;}50%{opacity:.5;}}" +
    ".rk-chat-header h3{margin:0;font-size:14px;font-weight:600;line-height:1.2;}" +
    ".rk-chat-header p{margin:2px 0 0;font-size:11px;opacity:.85;}" +
    ".rk-chat-messages{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:" + colors.bg + ";}" +
    ".rk-msg{max-width:85%;padding:9px 12px;border-radius:14px;font-size:13px;line-height:1.45;word-wrap:break-word;white-space:pre-wrap;}" +
    ".rk-msg.user{align-self:flex-end;background:" + cfg.accent + ";color:#fff;border-bottom-right-radius:4px;}" +
    ".rk-msg.bot{align-self:flex-start;background:" + colors.input + ";color:" + colors.text + ";border:1px solid " + colors.border + ";border-bottom-left-radius:4px;}" +
    ".rk-msg.bot.error{border-color:#ef4444;color:#ef4444;}" +
    ".rk-msg.bot.streaming::after{content:'▍';animation:rkblink 1s steps(2,start) infinite;color:" + cfg.accent + ";}" +
    "@keyframes rkblink{to{visibility:hidden;}}" +
    ".rk-chat-input{padding:12px;border-top:1px solid " + colors.border + ";display:flex;gap:8px;background:" + colors.panel + ";flex-shrink:0;}" +
    ".rk-chat-input input{flex:1;padding:9px 12px;background:" + colors.input + ";color:" + colors.text + ";border:1px solid " + colors.border + ";border-radius:10px;font-size:13px;outline:none;}" +
    ".rk-chat-input input:focus{border-color:" + cfg.accent + ";}" +
    ".rk-chat-input button{width:36px;height:36px;background:" + cfg.accent + ";color:#fff;border:none;border-radius:10px;cursor:pointer;font-size:14px;flex-shrink:0;}" +
    ".rk-chat-input button:disabled{opacity:.4;cursor:not-allowed;}" +
    ".rk-chat-sources{padding:8px 12px;font-size:10px;color:" + colors.muted + ";background:" + colors.bg + ";border-top:1px solid " + colors.border + ";max-height:60px;overflow-y:auto;flex-shrink:0;}" +
    ".rk-chat-sources div{margin:2px 0;}" +
    ".rk-chat-sources b{color:" + cfg.accent + ";}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  var fab = document.createElement("button");
  fab.className = "rk-chat-fab";
  fab.setAttribute("aria-label", "Open chat");
  fab.innerHTML = "💬";
  document.body.appendChild(fab);

  var panel = document.createElement("div");
  panel.className = "rk-chat-panel";
  panel.innerHTML = "" +
    "<div class=\"rk-chat-header\">" +
      "<div class=\"dot\"></div>" +
      "<div><h3>" + escapeHtml(cfg.title) + "</h3><p>" + escapeHtml(cfg.subtitle) + "</p></div>" +
    "</div>" +
    "<div class=\"rk-chat-messages\"></div>" +
    "<div class=\"rk-chat-sources\" style=\"display:none\"></div>" +
    "<div class=\"rk-chat-input\">" +
      "<input type=\"text\" placeholder=\"Type your message…\" />" +
      "<button aria-label=\"Send\">➤</button>" +
    "</div>";
  document.body.appendChild(panel);

  var messagesEl = panel.querySelector(".rk-chat-messages");
  var sourcesEl = panel.querySelector(".rk-chat-sources");
  var inputEl = panel.querySelector("input");
  var sendBtn = panel.querySelector("button");

  var sessionId = null;
  var isStreaming = false;
  var currentBotMsg = null;

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" })[c];
    });
  }

  function addMessage(role, text) {
    var div = document.createElement("div");
    div.className = "rk-msg " + role;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return div;
  }

  fab.addEventListener("click", function () {
    panel.classList.toggle("open");
    if (panel.classList.contains("open") && messagesEl.children.length === 0) {
      addMessage("bot", cfg.greeting);
      inputEl.focus();
    }
  });

  function setStreaming(on) {
    isStreaming = on;
    inputEl.disabled = on;
    sendBtn.disabled = on;
    sendBtn.textContent = on ? "■" : "➤";
  }

  sendBtn.addEventListener("click", send);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  function send() {
    if (isStreaming) {
      // stop streaming
      if (window.__rkAbort) window.__rkAbort();
      return;
    }
    var text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = "";
    addMessage("user", text);
    currentBotMsg = addMessage("bot", "");
    currentBotMsg.classList.add("streaming");
    sourcesEl.style.display = "none";
    sourcesEl.innerHTML = "";
    setStreaming(true);

    var body = JSON.stringify({ message: text, session_id: sessionId });
    fetch(cfg.apiUrl + "/api/integrate/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: body,
    })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        var reader = r.body.getReader();
        var decoder = new TextDecoder();
        var buffer = "";
        window.__rkAbort = function () { try { reader.cancel(); } catch (e) {} };
        function pump() {
          return reader.read().then(function (res) {
            if (res.done) return;
            buffer += decoder.decode(res.value, { stream: true });
            var idx;
            while ((idx = buffer.indexOf("\n\n")) >= 0) {
              var raw = buffer.slice(0, idx);
              buffer = buffer.slice(idx + 2);
              raw.split("\n").forEach(function (line) {
                if (!line.startsWith("data: ")) return;
                var payload;
                try { payload = JSON.parse(line.slice(6)); } catch (e) { return; }
                handleEvent(payload);
              });
            }
            return pump();
          });
        }
        return pump();
      })
      .catch(function (err) {
        if (currentBotMsg) {
          currentBotMsg.classList.remove("streaming");
          currentBotMsg.classList.add("error");
          currentBotMsg.textContent = "Error: " + err.message;
        }
      })
      .then(function () { setStreaming(false); currentBotMsg = null; });
  }

  function handleEvent(payload) {
    if (!payload || !currentBotMsg) return;
    if (payload.type === "token") {
      currentBotMsg.textContent += payload.content || "";
      messagesEl.scrollTop = messagesEl.scrollHeight;
    } else if (payload.type === "sources" && payload.sources && payload.sources.length) {
      sourcesEl.style.display = "block";
      sourcesEl.innerHTML = "<b>Sources:</b> " + payload.sources.map(escapeHtml).join(", ");
    } else if (payload.type === "done") {
      currentBotMsg.classList.remove("streaming");
      if (payload.session_id) sessionId = payload.session_id;
    } else if (payload.type === "error") {
      currentBotMsg.classList.remove("streaming");
      currentBotMsg.classList.add("error");
      currentBotMsg.textContent = payload.message || "Stream error";
    }
  }
})();
