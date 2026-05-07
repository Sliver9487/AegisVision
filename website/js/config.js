const APP_CONFIG = {
  DEFAULT_API_BASE_URL: "http://127.0.0.1:8000",
  ANALYZE_ENDPOINT: "/analyze_frame",
  HEALTH_ENDPOINT: "/health",
  EVENTS_ENDPOINT: "/events",
  DEVICES_ENDPOINT: "/devices",
  WS_ENDPOINT: "/ws",
  DEFAULT_INTERVAL_MS: 300,
  DEFAULT_JPEG_QUALITY: 0.7,
  DEFAULT_RESOLUTION: "480p"
};

function getApiBaseUrl() {
  return (localStorage.getItem("apiBaseUrl") || APP_CONFIG.DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function setApiBaseUrl(url) {
  localStorage.setItem("apiBaseUrl", url.trim().replace(/\/$/, ""));
}

function buildApiUrl(endpoint) {
  return `${getApiBaseUrl()}${endpoint}`;
}

function buildWsUrl() {
  const base = getApiBaseUrl();
  return base.replace(/^http/, "ws") + APP_CONFIG.WS_ENDPOINT;
}

