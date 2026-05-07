class ReconnectingWebSocketClient {
  constructor({ onOpen, onClose, onMessage, onError } = {}) {
    this.socket = null;
    this.retryMs = 1000;
    this.maxRetryMs = 10000;
    this.closedByUser = false;
    this.handlers = { onOpen, onClose, onMessage, onError };
  }

  connect() {
    this.closedByUser = false;
    this.socket = new WebSocket(buildWsUrl());
    this.socket.onopen = () => {
      this.retryMs = 1000;
      this.handlers.onOpen?.();
    };
    this.socket.onmessage = (event) => {
      try {
        this.handlers.onMessage?.(JSON.parse(event.data));
      } catch (error) {
        console.error("Invalid WebSocket message", error);
      }
    };
    this.socket.onerror = (event) => this.handlers.onError?.(event);
    this.socket.onclose = () => {
      this.handlers.onClose?.();
      if (!this.closedByUser) {
        setTimeout(() => this.connect(), this.retryMs);
        this.retryMs = Math.min(this.retryMs * 1.7, this.maxRetryMs);
      }
    };
  }

  close() {
    this.closedByUser = true;
    this.socket?.close();
  }
}

