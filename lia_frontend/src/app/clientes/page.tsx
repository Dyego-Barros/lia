"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { InteractiveTable } from "@/components/interactive-table-lazy";
import type { TableColumn } from "@/components/interactive-table";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";

type Cliente = { id?: number; nome: string; email?: string | null; telefone?: string | null; status?: boolean | null };
const empty = { nome: "", email: "", telefone: "", status: true };

export default function ClientesPage() {
  const [items, setItems] = useState<Cliente[]>([]); const [form, setForm] = useState(empty); const [editing, setEditing] = useState<number | null>(null); const [open, setOpen] = useState(false); const [busy, setBusy] = useState(false); const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { if (!message) return; const timer = window.setTimeout(() => setMessage(null), 5000); return () => window.clearTimeout(timer); }, [message]);
  async function load() { setItems(await apiGet<Cliente[]>("/clientes/")); }
  useEffect(() => { apiGet<Cliente[]>("/clientes/").then(setItems).catch((e) => console.error("Falha ao carregar clientes", e)); }, []);
  function start(item?: Cliente) { setEditing(item?.id ?? null); setForm(item ? { nome: item.nome, email: item.email ?? "", telefone: item.telefone ?? "", status: item.status !== false } : empty); setOpen(true); setMessage(null); }
  async function save(event: FormEvent) { event.preventDefault(); setBusy(true); try { const payload = { ...form, email: form.email || null, telefone: form.telefone || null }; if (editing) await apiPut(`/clientes/${editing}`, payload); else await apiPost("/clientes/", payload); await load(); setOpen(false); setMessage("Cliente salvo com sucesso."); } catch (e) { setMessage(e instanceof Error ? e.message : "Não foi possível salvar."); } finally { setBusy(false); } }
  async function remove(id: number) { if (!window.confirm("Excluir este cliente?")) return; try { await apiDelete(`/clientes/${id}`); await load(); setMessage("Cliente excluído."); } catch (e) { setMessage(e instanceof Error ? e.message : "Não foi possível excluir."); } }
  const columns = useMemo<TableColumn<Cliente>[]>(() => [
    { title: "Nome", data: "nome" }, { title: "Telefone", data: "telefone", render: (row) => row.telefone || "—" }, { title: "E-mail", data: "email", render: (row) => row.email || "—" },
    { title: "Status", data: "status", render: (row) => `<span class=\"status-pill ${row.status === false ? "status-inactive" : "status-active"}\">${row.status === false ? "Inativo" : "Ativo"}</span>` },
    { title: "Ações", data: "id", render: (row) => `<button class=\"table-action table-edit\" data-table-action=\"edit\" data-id=\"${row.id}\">Editar</button><button class=\"table-action table-delete\" data-table-action=\"delete\" data-id=\"${row.id}\">Excluir</button>` },
  ], []);
  function handleAction(action: string, id: number) { const item = items.find((entry) => entry.id === id); if (action === "edit" && item) start(item); if (action === "delete") remove(id); }
  return <div className="space-y-6"><header className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between"><div><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Clientes</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Cadastro e acompanhamento</h1></div><button onClick={() => start()} className="inline-flex items-center justify-center gap-2 rounded-xl bg-fuchsia-700 px-4 py-2 text-sm font-medium text-white hover:bg-fuchsia-800"><Plus size={16} /> Novo cliente</button></header>{message && <p className="rounded-xl border border-fuchsia-200 bg-fuchsia-50 p-3 text-sm text-fuchsia-800">{message}</p>}<section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><InteractiveTable data={items} columns={columns} onAction={handleAction} /></section>{open && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4"><form onSubmit={save} className="w-full max-w-lg space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xl"><div className="flex items-center justify-between"><h2 className="text-xl font-semibold text-slate-900">{editing ? "Editar cliente" : "Novo cliente"}</h2><button type="button" onClick={() => setOpen(false)}><X /></button></div><input required minLength={3} className="field" placeholder="Nome completo" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} /><input className="field" placeholder="Telefone" value={form.telefone} onChange={(e) => setForm({ ...form, telefone: e.target.value })} /><input type="email" className="field" placeholder="E-mail" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />{editing && <label className="flex items-center gap-2 text-sm text-slate-600"><input type="checkbox" checked={form.status} onChange={(e) => setForm({ ...form, status: e.target.checked })} /> Cliente ativo</label>}<button disabled={busy} className="w-full rounded-xl bg-fuchsia-700 px-4 py-3 font-medium text-white disabled:opacity-50">{busy ? "Salvando..." : "Salvar"}</button></form></div>}</div>;
}
