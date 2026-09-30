"use client";

import * as React from "react";
import { sessionSocketUrl } from "@/lib/api";

export interface SocketEvent {
  event_type: string;
  payload?: Record<string, unknown>;
}

export type SocketStatus = "idle" | "connecting" | "open" | "closed" | "error";

const CLOSE_REASONS: Record<number, string> = {
  4401: "Your session has expired. Please sign in again.",
  4403: "You do not have access to this session.",
};

/**
 * Live session connection for interviews/communication. The backend authenticates via ?token=
 * and only accepts the session owner. Call `connect(sessionId)` after creating the session.
 */
export function useSessionSocket(kind: "interviews" | "communication", onEvent: (event: SocketEvent) => void) {
  const socketRef = React.useRef<WebSocket | null>(null);
  const handlerRef = React.useRef(onEvent);
  const [status, setStatus] = React.useState<SocketStatus>("idle");
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    handlerRef.current = onEvent;
  }, [onEvent]);

  const close = React.useCallback(() => {
    socketRef.current?.close();
    socketRef.current = null;
  }, []);

  const connect = React.useCallback(
    (sessionId: string) =>
      new Promise<void>((resolve, reject) => {
        close();
        setStatus("connecting");
        setError(null);
        const socket = new WebSocket(sessionSocketUrl(kind, sessionId));
        socketRef.current = socket;

        socket.onopen = () => {
          setStatus("open");
          resolve();
        };
        socket.onmessage = (message) => {
          try {
            handlerRef.current(JSON.parse(message.data as string) as SocketEvent);
          } catch {
            /* ignore malformed frames */
          }
        };
        socket.onerror = () => {
          setStatus("error");
        };
        socket.onclose = (event) => {
          setStatus("closed");
          const reason = CLOSE_REASONS[event.code];
          if (reason) setError(reason);
          if (socketRef.current === socket) socketRef.current = null;
          reject(new Error(reason ?? "Could not open the live connection."));
        };
      }),
    [kind, close]
  );

  const send = React.useCallback((event: SocketEvent) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setError("The live connection is not open. Start a new session.");
      return false;
    }
    socket.send(JSON.stringify(event));
    return true;
  }, []);

  React.useEffect(() => close, [close]);

  return { status, error, setError, connect, send, close };
}
