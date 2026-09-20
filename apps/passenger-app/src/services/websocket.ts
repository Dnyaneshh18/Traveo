/**
 * Traveo Real-time WebSocket Client
 * Connects to FastAPI WebSocket endpoint at /ws?token=<jwt>
 */

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Map<string, (data: any) => void> = new Map();
  private isConnecting: boolean = false;

  connect(token: string) {
    if (this.socket || this.isConnecting) return;
    this.isConnecting = true;

    const wsUrl = `ws://localhost:8000/ws?token=${token}`;

    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        this.isConnecting = false;
        console.log('⚡ WebSocket Connected');
      };

      this.socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          // Backend sends { event: "EventName", payload: { ... }, timestamp: "..." }
          const callback = this.listeners.get(message.event);
          if (callback) {
            callback(message.payload);
          }
        } catch (e) {
          console.error('Error parsing WS message:', e);
        }
      };

      this.socket.onclose = () => {
        this.isConnecting = false;
        this.socket = null;
        console.log('WebSocket Connection Closed');
      };

      this.socket.onerror = (err) => {
        this.isConnecting = false;
        console.warn('WebSocket Error:', err);
      };
    } catch (e) {
      this.isConnecting = false;
      console.warn('WebSocket Client Error:', e);
    }
  }

  on(event: string, callback: (data: any) => void) {
    this.listeners.set(event, callback);
  }

  off(event: string) {
    this.listeners.delete(event);
  }

  sendPing() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send('ping');
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export const wsClient = new WebSocketClient();
