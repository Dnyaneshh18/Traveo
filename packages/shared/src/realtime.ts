/**
 * Realtime client — thin wrapper over WebSocket with reconnect/backoff,
 * topic subscriptions and a tiny event emitter.  Works in RN and browsers.
 */

import type { RealtimeMessage } from './types';

type Listener = (payload: any, message: RealtimeMessage) => void;
export type ConnectionState = 'idle' | 'connecting' | 'open' | 'closed';

export interface RealtimeOptions {
  url: () => string | null; // resolves the (token-bearing) URL at connect time
  onStateChange?: (state: ConnectionState) => void;
  maxBackoffMs?: number;
}

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private listeners = new Map<string, Set<Listener>>();
  private topics = new Set<string>();
  private backoff = 1000;
  private shouldRun = false;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  state: ConnectionState = 'idle';
  lastMessageAt = 0;

  constructor(private readonly opts: RealtimeOptions) {}

  connect() {
    this.shouldRun = true;
    this.open();
  }

  disconnect() {
    this.shouldRun = false;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.ws?.close();
    this.ws = null;
    this.setState('closed');
  }

  /** Force a fresh connection (e.g. after login/logout changes the token). */
  reset() {
    this.disconnect();
    this.backoff = 1000;
    this.connect();
  }

  subscribe(topic: string) {
    this.topics.add(topic);
    this.send({ type: 'subscribe', topic });
  }

  unsubscribe(topic: string) {
    this.topics.delete(topic);
    this.send({ type: 'unsubscribe', topic });
  }

  sendLocation(loc: { lat: number; lng: number; heading?: number | null; speed?: number | null; accuracy?: number | null }) {
    return this.send({ type: 'location', ...loc });
  }

  on(event: string, listener: Listener): () => void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  /** Listen to every event ("*"). */
  onAny(listener: Listener) {
    return this.on('*', listener);
  }

  private send(data: unknown): boolean {
    if (this.ws && this.ws.readyState === 1) {
      this.ws.send(JSON.stringify(data));
      return true;
    }
    return false;
  }

  private setState(state: ConnectionState) {
    if (this.state === state) return;
    this.state = state;
    this.opts.onStateChange?.(state);
  }

  private open() {
    if (!this.shouldRun) return;
    const url = this.opts.url();
    if (!url) {
      this.scheduleReconnect();
      return;
    }
    this.setState('connecting');
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }
    this.ws = ws;
    ws.onopen = () => {
      this.backoff = 1000;
      this.setState('open');
      for (const t of this.topics) this.send({ type: 'subscribe', topic: t });
    };
    ws.onmessage = (ev) => {
      this.lastMessageAt = Date.now();
      let msg: RealtimeMessage;
      try {
        msg = JSON.parse(typeof ev.data === 'string' ? ev.data : String(ev.data));
      } catch {
        return;
      }
      if (msg.type === 'ping') {
        this.send({ type: 'pong' });
        return;
      }
      this.listeners.get(msg.type)?.forEach((l) => l(msg.payload, msg));
      this.listeners.get('*')?.forEach((l) => l(msg.payload, msg));
    };
    ws.onerror = () => {
      /* onclose follows */
    };
    ws.onclose = () => {
      if (this.ws === ws) this.ws = null;
      this.setState('closed');
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect() {
    if (!this.shouldRun || this.reconnectTimer) return;
    const delay = this.backoff;
    this.backoff = Math.min(this.backoff * 1.8, this.opts.maxBackoffMs ?? 15000);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.open();
    }, delay);
  }
}
