"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, FileText, MessageSquare, Paperclip, RefreshCw, Send, X } from "lucide-react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import { ContactAvatar } from "@/components/contact-avatar";
import { NotificationAlert } from "@/components/notification-alert";
import { useConversationEvent } from "@/components/conversation-events";

type Conversation = { id: string; telefone: string; nome_contato: string | null; foto_perfil?: string | null; status: string; ultima_mensagem_em: string; nao_lidas: number };
type Message = { id: string; direcao: string; origem: string; tipo: string; conteudo: string; enviado_em: string; arquivo_nome?: string | null; mime_type?: string | null; arquivo_url?: string | null };
type ConversationPage = { items: Conversation[]; page: number; page_size: number; total: number; total_pages: number };
type MessagePage = { items: Message[]; has_more: boolean; next_before: string | null };
type SyncResult = { conversas: number; mensagens_examinadas: number; mensagens_importadas: number; sincronizacoes_em_andamento: number; falhas: { conversation_id: string; erro: string }[] };
type Notice = { message: string; type: "success" | "warning" | "error" };
const MAX_FILE_BYTES = 10 * 1024 * 1024;
const PAGE_SIZE = 20;
const MESSAGE_PAGE_SIZE = 50;
const originLabels: Record<string, string> = { cliente: "Cliente", ia: "IA", atendente_plataforma: "Atendente", atendente_whatsapp: "WhatsApp", sistema: "Sistema", desconhecida: "Enviada" };

function fileBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Não foi possível ler o arquivo."));
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1] ?? "");
    reader.readAsDataURL(file);
  });
}

function Attachment({ message }: { message: Message }) {
  if (!message.arquivo_url || !message.mime_type) return <p>{message.conteudo}</p>;
  const caption = message.conteudo !== message.arquivo_nome && <p className="mt-2">{message.conteudo}</p>;
  if (message.mime_type.startsWith("image/")) return <><img src={message.arquivo_url} alt={message.arquivo_nome ?? "Imagem enviada"} className="max-h-80 rounded-lg object-contain" />{caption}</>;
  if (message.mime_type.startsWith("video/")) return <><video controls preload="metadata" className="max-h-80 max-w-full rounded-lg"><source src={message.arquivo_url} type={message.mime_type} /></video>{caption}</>;
  if (message.mime_type.startsWith("audio/")) return <audio controls preload="metadata" className="max-w-full"><source src={message.arquivo_url} type={message.mime_type} /></audio>;
  return <a href={message.arquivo_url} download={message.arquivo_nome ?? true} className="flex items-center gap-2 font-medium underline"><FileText size={18} />{message.arquivo_nome ?? message.conteudo}</a>;
}

export default function ConversasPage() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [sending, setSending] = useState(false);
  const [closing, setClosing] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const fileInput = useRef<HTMLInputElement>(null);
  const messagesEnd = useRef<HTMLDivElement>(null);
  const scrollToLatest = useRef(false);
  const eventTimer = useRef<number | null>(null);
  const conversationEvent = useConversationEvent();
  useEffect(() => { if (!error) return; const timer = window.setTimeout(() => setError(null), 5000); return () => window.clearTimeout(timer); }, [error]);
  useEffect(() => { if (!notice) return; const timer = window.setTimeout(() => setNotice(null), 6000); return () => window.clearTimeout(timer); }, [notice]);
  useEffect(() => {
    if (!scrollToLatest.current) return;
    scrollToLatest.current = false;
    window.requestAnimationFrame(() => messagesEnd.current?.scrollIntoView({ block: "end" }));
  }, [messages]);

  const load = useCallback(async (requestedPage: number) => {
    try {
      const result = await apiGet<ConversationPage>(`/integracoes/conversas?page=${requestedPage}&page_size=${PAGE_SIZE}`);
      setItems(result.items);
      setTotal(result.total);
      setTotalPages(result.total_pages);
      if (result.page !== requestedPage) setPage(result.page);
      setSelected((current) => current ? result.items.find((item) => item.id === current.id) ?? current : null);
    } catch (reason) { console.error("Falha ao carregar conversas", reason); }
  }, []);
  const loadMessages = useCallback(async (conversationId: string, before?: string) => {
    const query = new URLSearchParams({ limit: String(MESSAGE_PAGE_SIZE) });
    if (before) query.set("before", before);
    const result = await apiGet<MessagePage>(`/integracoes/conversas/${conversationId}/mensagens?${query}`);
    setMessages((current) => before
      ? [...result.items, ...current.filter((message) => !result.items.some((item) => item.id === message.id))]
      : result.items);
    setNextBefore(result.next_before);
    setItems((current) => current.map((item) => item.id === conversationId ? { ...item, nao_lidas: 0 } : item));
  }, []);
  const refreshConversation = useCallback(async (conversationId: string) => {
    const conversation = await apiGet<Conversation>(`/integracoes/conversas/${conversationId}/resumo`);
    setItems((current) => {
      const next = [conversation, ...current.filter((item) => item.id !== conversation.id)]
        .sort((first, second) => second.ultima_mensagem_em.localeCompare(first.ultima_mensagem_em))
        .slice(0, PAGE_SIZE);
      return next;
    });
    setSelected((current) => current?.id === conversation.id ? conversation : current);
  }, []);
  async function open(item: Conversation) {
    try { scrollToLatest.current = true; setSelected({ ...item, nao_lidas: 0 }); await loadMessages(item.id); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao carregar mensagens."); }
  }
  async function loadOlderMessages() {
    if (!selected || !nextBefore || loadingOlder) return;
    setLoadingOlder(true);
    try { await loadMessages(selected.id, nextBefore); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Falha ao carregar mensagens anteriores."); }
    finally { setLoadingOlder(false); }
  }
  async function closeConversation() {
    if (!selected || closing) return;
    setClosing(true); setError(null);
    try {
      await apiPatch(`/integracoes/conversas/${selected.id}`, { status: "encerrada" });
      setSelected(null); setMessages([]); setNextBefore(null);
      setNotice({ message: "Conversa encerrada. Uma nova mensagem do cliente irá reabri-la automaticamente.", type: "success" });
      await load(page);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível encerrar a conversa.");
    } finally { setClosing(false); }
  }
  async function syncOpenwa() {
    if (syncing) return;
    setSyncing(true); setNotice(null); setError(null);
    try {
      const result = await apiPost<SyncResult>("/integracoes/conversas/sincronizar-openwa");
      await load(page);
      if (selected) await loadMessages(selected.id);
      const importedLabel = result.mensagens_importadas === 1 ? "mensagem importada" : "mensagens importadas";
      const details = `${result.mensagens_importadas} ${importedLabel} de ${result.conversas} conversa${result.conversas === 1 ? "" : "s"}.`;
      setNotice(result.falhas.length
        ? { message: `Sincronização concluída com ${result.falhas.length} falha${result.falhas.length === 1 ? "" : "s"}. ${details} Motivo: ${result.falhas[0].erro}`, type: "warning" }
        : { message: `Sincronização concluída. ${details}`, type: "success" });
    } catch (reason) {
      setNotice({ message: reason instanceof Error ? reason.message : "Não foi possível sincronizar o OpenWA.", type: "error" });
    } finally { setSyncing(false); }
  }
  async function send(event: FormEvent) {
    event.preventDefault();
    if (!selected || (!text.trim() && !file)) return;
    setSending(true); setError(null);
    try {
      const message = file
        ? await apiPost<Message>(`/integracoes/conversas/${selected.id}/arquivos`, { nome: file.name, mime_type: file.type || "application/octet-stream", base64: await fileBase64(file), legenda: text.trim() })
        : await apiPost<Message>(`/integracoes/conversas/${selected.id}/mensagens`, { conteudo: text.trim() });
      scrollToLatest.current = true;
      setMessages((current) => current.some((item) => item.id === message.id) ? current : [...current, message]); setText(""); setFile(null);
      if (fileInput.current) fileInput.current.value = "";
      await load(page);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Não foi possível enviar a mensagem."); }
    finally { setSending(false); }
  }
  function selectFile(next?: File) {
    if (!next) return;
    if (next.size > MAX_FILE_BYTES) { setError("O arquivo deve ter no máximo 10 MB."); if (fileInput.current) fileInput.current.value = ""; return; }
    setFile(next);
  }
  useEffect(() => { void Promise.resolve().then(() => load(page)); const interval = window.setInterval(() => void load(page), 60000); return () => window.clearInterval(interval); }, [load, page]);
  useEffect(() => {
    if (!conversationEvent) return;
    if (eventTimer.current) window.clearTimeout(eventTimer.current);
    eventTimer.current = window.setTimeout(() => {
      if (!conversationEvent.conversation_id) {
        void load(page);
        return;
      }
      void refreshConversation(conversationEvent.conversation_id).catch(() => void load(page));
      if (selected?.id === conversationEvent.conversation_id) void loadMessages(selected.id).catch(() => undefined);
    }, 150);
    return () => { if (eventTimer.current) window.clearTimeout(eventTimer.current); };
  }, [conversationEvent, load, loadMessages, page, refreshConversation, selected?.id]);

  return <div className="flex min-h-0 flex-col gap-6 lg:h-[calc(100vh-12rem)] lg:overflow-hidden">
    <header className="flex shrink-0 flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:flex-row sm:items-center sm:justify-between"><div><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">Mayssa · WhatsApp</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Conversas</h1><p className="mt-2 text-sm text-slate-500">Consulte o histórico e responda aos clientes pelo provedor da conversa.</p></div><div className="flex items-center gap-2"><button type="button" onClick={() => void syncOpenwa()} disabled={syncing} className="inline-flex items-center justify-center gap-2 rounded-xl bg-fuchsia-700 px-4 py-2 text-sm font-medium text-white hover:bg-fuchsia-800 disabled:cursor-wait disabled:opacity-60"><RefreshCw size={16} className={syncing ? "animate-spin" : ""} />{syncing ? "Sincronizando..." : "Sincronizar OpenWA"}</button><button type="button" onClick={() => void load(page)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100" title="Atualizar conversas" aria-label="Atualizar conversas"><RefreshCw size={18} /></button></div></header>
    <NotificationAlert message={error} type="error" />
    <NotificationAlert message={notice?.message ?? null} type={notice?.type} />
    <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[320px_1fr]">
      <section className="flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"><div className="flex shrink-0 items-center justify-between px-3 py-2"><h2 className="font-semibold text-slate-900">Todas as conversas</h2><span className="text-xs text-slate-500">{total} no total</span></div><div className="min-h-0 flex-1 space-y-1 overflow-y-auto">{items.map((item) => <button key={item.id} onClick={() => void open(item)} className={`w-full rounded-xl p-3 text-left hover:bg-fuchsia-50 ${selected?.id === item.id ? "bg-fuchsia-50" : ""}`}><div className="flex items-center gap-3"><ContactAvatar photoUrl={item.foto_perfil} size="medium" /><div className="min-w-0 flex-1"><div className="flex items-center justify-between gap-2"><p className="truncate font-medium text-slate-900">{item.nome_contato || item.telefone}</p>{item.nao_lidas > 0 && <span className="inline-flex min-w-5 items-center justify-center rounded-full bg-emerald-500 px-1.5 py-0.5 text-[11px] font-bold text-white" aria-label={`${item.nao_lidas} mensagens não lidas`}>{item.nao_lidas > 99 ? "99+" : item.nao_lidas}</span>}</div><p className="truncate text-xs text-slate-500">{item.nome_contato ? item.telefone : `${item.telefone} · ${item.status}`}</p></div></div></button>)}{!items.length && <p className="p-3 text-sm text-slate-500">Nenhuma conversa recebida.</p>}</div><nav className="flex shrink-0 items-center justify-between border-t border-slate-100 px-2 pt-3" aria-label="Paginação das conversas"><button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page <= 1} className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Página anterior"><ChevronLeft size={17} /></button><span className="text-xs text-slate-500">Página {page} de {totalPages}</span><button type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page >= totalPages} className="rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Próxima página"><ChevronRight size={17} /></button></nav></section>
      <section className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">{selected ? <><div className="flex shrink-0 items-center justify-between border-b border-slate-100 p-5"><div className="flex items-center gap-3"><ContactAvatar photoUrl={selected.foto_perfil} size="large" /><div><h2 className="font-semibold text-slate-900">{selected.nome_contato || selected.telefone}</h2><p className="text-sm text-slate-500">{selected.telefone}</p></div></div><button type="button" onClick={() => void closeConversation()} disabled={closing} className="rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50 disabled:cursor-wait disabled:opacity-60">{closing ? "Encerrando..." : "Encerrar"}</button></div><div className="flex min-h-0 flex-1 flex-col"><div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-5">{nextBefore && <div className="text-center"><button type="button" onClick={() => void loadOlderMessages()} disabled={loadingOlder} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-50 disabled:opacity-50">{loadingOlder ? "Carregando..." : "Carregar mensagens anteriores"}</button></div>}{messages.map((item) => <div key={item.id} className={`max-w-[80%] rounded-xl p-3 text-sm ${item.direcao === "saida" ? "ml-auto bg-fuchsia-100 text-fuchsia-950" : "bg-slate-100 text-slate-800"}`}><span className="mb-1 block text-[10px] font-semibold uppercase tracking-wide opacity-60">{originLabels[item.origem] ?? item.origem}</span><Attachment message={item} /><time className="mt-1 block text-[11px] opacity-60">{new Date(item.enviado_em).toLocaleString("pt-BR")}</time></div>)}<div ref={messagesEnd} aria-hidden="true" /></div><form onSubmit={send} className="shrink-0 border-t border-slate-100 p-4">{file && <div className="mb-2 flex items-center justify-between rounded-lg bg-slate-100 px-3 py-2 text-sm"><span className="truncate">{file.name}</span><button type="button" onClick={() => setFile(null)} aria-label="Remover arquivo"><X size={16} /></button></div>}<div className="flex gap-2"><input ref={fileInput} type="file" className="hidden" onChange={(event) => selectFile(event.target.files?.[0])} /><button type="button" onClick={() => fileInput.current?.click()} disabled={sending} className="rounded-xl border border-slate-200 px-3 text-slate-600 hover:bg-slate-50" title="Anexar arquivo"><Paperclip size={19} /></button><input className="field" placeholder={file ? "Legenda (opcional)" : "Digite uma mensagem para o cliente"} value={text} onChange={(event) => setText(event.target.value)} disabled={sending} /><button disabled={sending || (!text.trim() && !file)} className="primary-button w-auto px-5" title="Enviar"><Send size={16} />Enviar</button></div></form></div></> : <div className="flex min-h-[420px] flex-1 items-center justify-center text-slate-400"><MessageSquare size={22} className="mr-2" />Selecione uma conversa</div>}</section>
    </div>
  </div>;
}
