"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { MessageSquare, RefreshCw, Send } from "lucide-react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { ContactAvatar } from "@/components/contact-avatar";

type Conversation = { id: string; telefone: string; nome_contato: string | null; foto_perfil?: string | null; status: string; ultima_mensagem_em: string; ultima_mensagem_recebida?: { id: string; enviado_em: string } | null };
type Message = { id: string; direcao: string; conteudo: string; enviado_em: string };

export default function ConversasPage() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { if (!error) return; const timer = window.setTimeout(() => setError(null), 5000); return () => window.clearTimeout(timer); }, [error]);
  const [sending, setSending] = useState(false);
  const [newConversationIds, setNewConversationIds] = useState<string[]>([]);
  const itemsRef = useRef<Conversation[]>([]);

  async function load(initial = false) {
    try {
      const next = await apiGet<Conversation[]>("/integracoes/conversas");
      if (!initial) {
        const previous = itemsRef.current;
        const changed = next.filter((item) => {
          const old = previous.find((conversation) => conversation.id === item.id);
          return item.ultima_mensagem_recebida?.enviado_em && item.ultima_mensagem_recebida.enviado_em !== old?.ultima_mensagem_recebida?.enviado_em;
        }).map((item) => item.id);
        if (changed.length) setNewConversationIds((current) => [...new Set([...current, ...changed])]);
      }
      itemsRef.current = next;
      setItems(next);
    } catch (e) { if (initial) console.error("Falha ao carregar conversas", e); }
  }
  async function open(item: Conversation) {
    try {
      setSelected(item);
      setNewConversationIds((current) => current.filter((id) => id !== item.id));
      setMessages(await apiGet<Message[]>(`/integracoes/conversas/${item.id}/mensagens`));
    } catch (e) { setError(e instanceof Error ? e.message : "Falha ao carregar mensagens."); }
  }
  async function closeConversation() { if (!selected) return; const nextStatus = selected.status === "humano" ? "aberta" : "encerrada"; await apiPatch(`/integracoes/conversas/${selected.id}`, { status: nextStatus }); setSelected({ ...selected, status: nextStatus }); await load(); }
  async function send(event: FormEvent) { event.preventDefault(); if (!selected || !text.trim()) return; setSending(true); setError(null); try { const message = await apiPost<Message>(`/integracoes/conversas/${selected.id}/mensagens`, { conteudo: text.trim() }); setMessages((current) => [...current, message]); setText(""); await load(); } catch (e) { setError(e instanceof Error ? e.message : "Não foi possível enviar a mensagem."); } finally { setSending(false); } }
  useEffect(() => {
    Promise.resolve().then(() => load(true));
    const interval = window.setInterval(() => load(), 5000);
    return () => window.clearInterval(interval);
  }, []);

  return <div className="flex min-h-0 flex-col gap-6 lg:h-[calc(100vh-12rem)] lg:overflow-hidden"><header className="flex shrink-0 items-center justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · WhatsApp</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Conversas</h1><p className="mt-2 text-sm text-slate-500">Consulte o histórico e responda aos clientes pelo provedor da conversa.</p></div><button onClick={() => load()} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" title="Atualizar"><RefreshCw size={18} /></button></header>{error && <p className="shrink-0 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}<div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[320px_1fr]"><section className="flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"><h2 className="shrink-0 px-3 py-2 font-semibold text-slate-900">Todas as conversas</h2>{newConversationIds.length > 0 && <button onClick={() => setNewConversationIds([])} className="mx-1 mb-2 shrink-0 rounded-xl border border-fuchsia-200 bg-fuchsia-50 px-3 py-2 text-left text-sm font-medium text-fuchsia-800">🔔 {newConversationIds.length === 1 ? "Nova mensagem recebida" : `${newConversationIds.length} novas mensagens recebidas`}</button>}<div className="min-h-0 flex-1 space-y-1 overflow-y-auto">{items.map((item) => <button key={item.id} onClick={() => open(item)} className={`w-full rounded-xl p-3 text-left hover:bg-fuchsia-50 ${selected?.id === item.id ? "bg-fuchsia-50" : ""}`}><div className="flex items-center gap-3"><ContactAvatar photoUrl={item.foto_perfil} size="medium" /><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className="truncate font-medium text-slate-900">{item.nome_contato || item.telefone}</p>{newConversationIds.includes(item.id) && <span className="h-2.5 w-2.5 shrink-0 rounded-full bg-fuchsia-600" title="Mensagem nova" />}</div><p className="truncate text-xs text-slate-500">{item.nome_contato ? item.telefone : `${item.telefone} · ${item.status}`}</p></div></div></button>)}{!items.length && <p className="p-3 text-sm text-slate-500">Nenhuma conversa recebida.</p>}</div></section><section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">{selected ? <><div className="flex shrink-0 items-center justify-between border-b border-slate-100 p-5"><div className="flex items-center gap-3"><ContactAvatar photoUrl={selected.foto_perfil} size="large" /><div><h2 className="font-semibold text-slate-900">{selected.nome_contato || selected.telefone}</h2><p className="text-sm text-slate-500">{selected.telefone}</p></div></div><button onClick={closeConversation} className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50">Encerrar</button></div><div className="flex min-h-0 flex-1 flex-col"><div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-5">{messages.map((item) => <div key={item.id} className={`max-w-[80%] rounded-xl p-3 text-sm ${item.direcao === "saida" ? "ml-auto bg-fuchsia-100 text-fuchsia-950" : "bg-slate-100 text-slate-800"}`}><p>{item.conteudo}</p><time className="mt-1 block text-[11px] opacity-60">{new Date(item.enviado_em).toLocaleString("pt-BR")}</time></div>)}</div><form onSubmit={send} className="flex shrink-0 gap-2 border-t border-slate-100 p-4"><input className="field" placeholder="Digite uma mensagem para o cliente" value={text} onChange={(e) => setText(e.target.value)} disabled={sending} /><button disabled={sending || !text.trim()} className="primary-button w-auto px-5" title="Enviar"><Send size={16} />Enviar</button></form></div></> : <div className="flex min-h-[420px] flex-1 items-center justify-center text-slate-400"><MessageSquare size={22} className="mr-2" />Selecione uma conversa</div>}</section></div></div>;
}
