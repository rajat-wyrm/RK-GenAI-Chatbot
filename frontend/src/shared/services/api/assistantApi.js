import { request } from "./request";

/**
 * Fetches starter prompt suggestions for the AI assistant UI.
 */
export const getAiSuggestions = () => request("/ai/suggestions");

/**
 * Fetches the current list of assistant capabilities.
 */
export const getAiCapabilities = () => request("/ai/capabilities");

/**
 * Fetches the welcome message shown when the assistant initializes.
 */
export const getAiWelcomeMessage = () => request("/ai/welcome-message");

/**
 * Synchronous chat — returns the full reply at once.
 */
export const sendAiChatMessage = (message, sessionId) =>
  request("/ai/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });

/**
 * Token-by-token streaming chat via Server-Sent Events.
 *
 * @param {string} message
 * @param {object} callbacks
 *   onSources?(sources)   — called with the list of source documents
 *   onToken?(token, provider) — called for each streamed token
 *   onDone?({session_id, provider, sources}) — called when the stream ends
 *   onError?(error)       — called on any error
 * @returns {Promise<{abort: () => void}>}
 */
export const streamAiChatMessage = async (message, { sessionId, onSources, onToken, onDone, onError } = {}) => {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api").replace(/\/$/, "");
  const url = `${baseUrl}/chat/stream`;

  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
  } catch (e) {
    onError?.(e);
    return { abort: () => {} };
  }

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "");
    onError?.(new Error(text || `HTTP ${response.status}`));
    return { abort: () => {} };
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const controller = new AbortController();

  const pump = (async () => {
    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buffer.indexOf("\n\n")) >= 0) {
          const raw = buffer.slice(0, idx);
          buffer = buffer.slice(idx + 2);
          if (!raw) continue;
          const dataLine = raw.split("\n").find((l) => l.startsWith("data: "));
          if (!dataLine) continue;
          let payload;
          try { payload = JSON.parse(dataLine.slice(6)); } catch { continue; }
          if (payload.type === "start") continue;
          if (payload.type === "sources") onSources?.(payload.sources || []);
          else if (payload.type === "token") onToken?.(payload.content, payload.provider);
          else if (payload.type === "done") onDone?.(payload);
          else if (payload.type === "error") onError?.(new Error(payload.message || "stream error"));
        }
      }
    } catch (e) {
      onError?.(e);
    }
  })();

  return {
    abort: () => {
      controller.abort();
      reader.cancel().catch(() => {});
    },
    done: pump,
  };
};

/**
 * Bootstraps the assistant UI by aggregating suggestions, capabilities, and welcome copy.
 */
export const getAiAssistantBootstrap = async () => {
  const [suggestionsResult, capabilitiesResult, welcomeResult] = await Promise.allSettled([
    getAiSuggestions(),
    getAiCapabilities(),
    getAiWelcomeMessage(),
  ]);

  if (
    suggestionsResult.status === "rejected" &&
    capabilitiesResult.status === "rejected" &&
    welcomeResult.status === "rejected"
  ) {
    throw new Error("AI assistant bootstrap unavailable");
  }

  return {
    suggestions:
      suggestionsResult.status === "fulfilled"
        ? suggestionsResult.value?.data ?? suggestionsResult.value ?? []
        : [],
    capabilities:
      capabilitiesResult.status === "fulfilled"
        ? capabilitiesResult.value?.data ?? capabilitiesResult.value ?? []
        : [],
    welcomeMessage:
      welcomeResult.status === "fulfilled"
        ? welcomeResult.value?.message || "Hello! How can I help you today?"
        : "Hello! How can I help you today?",
    partialData:
      suggestionsResult.status === "rejected" ||
      capabilitiesResult.status === "rejected" ||
      welcomeResult.status === "rejected",
  };
};
