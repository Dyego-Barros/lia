"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

type ConversationEvent = { conversation_id: string };

const ConversationEventsContext = createContext<ConversationEvent | null>(null);

export function ConversationEventsProvider({ children }: { children: React.ReactNode }) {
  const [event, setEvent] = useState<ConversationEvent | null>(null);

  useEffect(() => {
    const source = new EventSource(`${API_BASE_URL}/integracoes/conversas/eventos`, { withCredentials: true });
    source.onopen = () => setEvent({ conversation_id: "" });
    const changed = (rawEvent: Event) => {
      try {
        setEvent(JSON.parse((rawEvent as MessageEvent<string>).data) as ConversationEvent);
      } catch {
        // O fallback REST continua ativo caso um evento isolado seja inválido.
      }
    };
    source.addEventListener("conversations.changed", changed);
    return () => {
      source.onopen = null;
      source.removeEventListener("conversations.changed", changed);
      source.close();
    };
  }, []);

  return <ConversationEventsContext.Provider value={event}>{children}</ConversationEventsContext.Provider>;
}

export function useConversationEvent() {
  return useContext(ConversationEventsContext);
}
