"use client";

import { FormEvent, useEffect, useState } from "react";
import { Copy, Plus, Save, Trash2 } from "lucide-react";
import { apiDelete, apiGet, apiPost } from "@/lib/api";

type WhatsApp = { id: number; nome: string; tipo: string; prioridade: number; ativo: boolean; webhook_configurado: boolean; webhook_url: string; webhook_verify_token?: string | null };
type AI = { id: number; nome: string; tipo: string; modelo: string; base_url: string | null; prioridade: number; ativo: boolean };

export default function ConfiguracoesPage() {
  const [whatsapp, setWhatsapp] = useState<WhatsApp[]>([]);
  const [ai, setAi] = useState<AI[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { if (!message) return; const timer = window.setTimeout(() => setMessage(null), 5000); return () => window.clearTimeout(timer); }, [message]);
  const [waForm, setWaForm] = useState({ nome: "WhatsApp principal", tipo: "meta", prioridade: "1", credenciais: "{}", webhook_token: "" });
  const [aiForm, setAiForm] = useState({ nome: "Modelo principal", tipo: "openai", modelo: "gpt-4o-mini", base_url: "", prioridade: "1", api_key: "" });

  async function load() {
    const [w, models] = await Promise.all([apiGet<WhatsApp[]>("/integracoes/whatsapp"), apiGet<AI[]>("/integracoes/ia")]);
    setWhatsapp(w); setAi(models);
  }
  useEffect(() => { Promise.resolve().then(() => load()).catch((e) => console.error("Falha ao carregar configurações", e)); }, []);

  async function addWhatsApp(event: FormEvent) {
    event.preventDefault();
    try {
      await apiPost("/integracoes/whatsapp", { ...waForm, prioridade: Number(waForm.prioridade), credenciais: JSON.parse(waForm.credenciais) });
      setMessage("Provedor WhatsApp cadastrado."); await load();
    } catch (e) { setMessage(e instanceof Error ? e.message : "Não foi possível cadastrar o provedor."); }
  }

  async function addAI(event: FormEvent) {
    event.preventDefault();
    try {
      await apiPost("/integracoes/ia", { ...aiForm, prioridade: Number(aiForm.prioridade), base_url: aiForm.base_url || null });
      setMessage("Modelo de IA cadastrado."); setAiForm({ ...aiForm, api_key: "" }); await load();
    } catch (e) { setMessage(e instanceof Error ? e.message : "Não foi possível cadastrar o modelo."); }
  }

  async function remove(path: string) {
    if (!window.confirm("Remover esta integração?")) return;
    try { await apiDelete(path); setMessage("Integração removida."); await load(); } catch (e) { setMessage(e instanceof Error ? e.message : "Falha ao remover integração."); }
  }
  async function copyWebhook(url: string) { await navigator.clipboard.writeText(url); setMessage("URL do webhook copiada."); }

  return <div className="space-y-6">
    <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Configurações</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Integrações</h1><p className="mt-2 text-sm text-slate-500">Cadastre vários provedores, defina a prioridade e mantenha as credenciais protegidas no backend.</p></header>
    {message && <p className="rounded-xl border border-fuchsia-200 bg-fuchsia-50 p-3 text-sm text-fuchsia-800">{message}</p>}
    <div className="grid gap-4 xl:grid-cols-2">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Provedores WhatsApp</h2><div className="mt-4 space-y-2">{whatsapp.map((item) => <div key={item.id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3"><div><p className="font-medium">{item.nome} <span className="text-xs text-slate-500">({item.tipo})</span></p><p className="text-xs text-slate-500">Prioridade {item.prioridade} · Webhook {item.webhook_configurado ? "configurado" : "pendente"}</p></div><button onClick={() => remove(`/integracoes/whatsapp/${item.id}`)} className="rounded-lg p-2 text-rose-600 hover:bg-rose-50" title="Remover"><Trash2 size={16} /></button></div>)}</div><form onSubmit={addWhatsApp} className="mt-5 space-y-3 border-t border-slate-100 pt-5"><h3 className="font-semibold">Adicionar provedor</h3><input className="field" placeholder="Nome da integração" value={waForm.nome} onChange={(e) => setWaForm({ ...waForm, nome: e.target.value })} required /><select className="field select-field" value={waForm.tipo} onChange={(e) => setWaForm({ ...waForm, tipo: e.target.value })}><option value="meta">Meta Cloud API</option><option value="ultramsg">UltraMsg</option><option value="evolution">Evolution API</option><option value="openwa">OpenWA</option><option value="twilio">Twilio</option></select><input className="field" type="number" min="1" placeholder="Prioridade" value={waForm.prioridade} onChange={(e) => setWaForm({ ...waForm, prioridade: e.target.value })} required /><textarea className="field font-mono text-xs" placeholder={'OpenWA: {"base_url":"http://openwa:2785","api_key":"...","session_id":"..."}'} value={waForm.credenciais} onChange={(e) => setWaForm({ ...waForm, credenciais: e.target.value })} required /><input className="field" placeholder="Token HMAC do webhook" value={waForm.webhook_token} onChange={(e) => setWaForm({ ...waForm, webhook_token: e.target.value })} /><button className="primary-button"><Plus size={16} />Adicionar WhatsApp</button></form></section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Modelos e APIs de IA</h2><div className="mt-4 space-y-2">{ai.map((item) => <div key={item.id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-3"><div><p className="font-medium">{item.nome} <span className="text-xs text-slate-500">({item.tipo})</span></p><p className="text-xs text-slate-500">{item.modelo} · prioridade {item.prioridade}</p></div><button onClick={() => remove(`/integracoes/ia/${item.id}`)} className="rounded-lg p-2 text-rose-600 hover:bg-rose-50" title="Remover"><Trash2 size={16} /></button></div>)}</div><form onSubmit={addAI} className="mt-5 space-y-3 border-t border-slate-100 pt-5"><h3 className="font-semibold">Adicionar modelo</h3><input className="field" placeholder="Nome da integração" value={aiForm.nome} onChange={(e) => setAiForm({ ...aiForm, nome: e.target.value })} required /><select className="field select-field" value={aiForm.tipo} onChange={(e) => setAiForm({ ...aiForm, tipo: e.target.value })}><option value="openai">OpenAI</option><option value="groq">Groq</option><option value="ollama">Ollama</option><option value="anthropic">Anthropic</option><option value="custom">API compatível</option></select><input className="field" placeholder="Modelo" value={aiForm.modelo} onChange={(e) => setAiForm({ ...aiForm, modelo: e.target.value })} required /><input className="field" placeholder="Base URL (opcional)" value={aiForm.base_url} onChange={(e) => setAiForm({ ...aiForm, base_url: e.target.value })} /><input className="field" type="number" min="1" placeholder="Prioridade" value={aiForm.prioridade} onChange={(e) => setAiForm({ ...aiForm, prioridade: e.target.value })} required /><input className="field" type="password" placeholder="API key" value={aiForm.api_key} onChange={(e) => setAiForm({ ...aiForm, api_key: e.target.value })} required /><button className="primary-button"><Save size={16} />Adicionar modelo</button></form></section>
    </div>
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="font-semibold text-slate-900">URLs dos webhooks</h2><p className="mt-2 text-sm text-slate-500">Copie a URL correspondente e cole no painel do provedor. Configure PUBLIC_API_URL com um domínio público antes de usar em produção.</p><div className="mt-4 space-y-3">{whatsapp.map((item) => <div key={item.id} className="flex flex-col gap-2 md:flex-row md:items-center"><span className="w-40 text-sm font-medium text-slate-700">{item.nome}</span><input readOnly className="field text-xs" value={item.webhook_url} /><button type="button" onClick={() => copyWebhook(item.webhook_url)} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"><Copy size={15} />Copiar</button></div>)}</div></section>
    <section className="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-500 shadow-sm"><h2 className="font-semibold text-slate-900">Segurança e fallback</h2><p className="mt-2">As chaves são criptografadas antes de serem salvas e nunca retornam para o frontend. A prioridade dos modelos ativos define qual IA será usada primeiro.</p></section>
  </div>;
}
