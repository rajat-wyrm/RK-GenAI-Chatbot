const readBooleanEnv = (value, fallback = false) => {
  if (value === undefined) return fallback;
  return value === "true";
};

export const env = {
  appName: import.meta.env.VITE_APP_NAME || "RK Gen AI Chatbot",
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api",
  useMockApi: readBooleanEnv(import.meta.env.VITE_USE_MOCK_API, false),
};
