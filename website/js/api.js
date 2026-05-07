async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {})
    }
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function getHealth() {
  return fetchJson(buildApiUrl(APP_CONFIG.HEALTH_ENDPOINT));
}

function getEvents() {
  return fetchJson(buildApiUrl(APP_CONFIG.EVENTS_ENDPOINT));
}

function getDevices() {
  return fetchJson(buildApiUrl(APP_CONFIG.DEVICES_ENDPOINT));
}

function analyzeFrame(payload) {
  return fetchJson(buildApiUrl(APP_CONFIG.ANALYZE_ENDPOINT), {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

