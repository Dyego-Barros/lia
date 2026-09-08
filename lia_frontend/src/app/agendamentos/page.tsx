"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Download, Plus, X } from "lucide-react";
import { InteractiveTable } from "@/components/interactive-table-lazy";
import type { TableColumn } from "@/components/interactive-table";
import { apiDelete, apiGet, apiPost, apiPut } from "@/lib/api";
import { downloadCsv } from "@/lib/export";

type Appointment = { id?: number; cliente_id: number; procedimento_id: number; profissional_id?: number | null; data_hora: string; status: string; valor_cobrado?: number | null; forma_pagamento?: string | null; status_pagamento?: string };
type AppointmentRow = Appointment & { cliente_nome: string; procedimento_nome: string; profissional_nome: string };
type Client = { id?: number; nome: string };
type Procedure = { id?: number; nome: string; duracao: number };
type Professional = { id?: number; nome: string; ativo: boolean };
const empty = { cliente_nome: "", procedimento_id: "", profissional_id: "", data_hora: "", status: "pendente", valor_cobrado: "", forma_pagamento: "", status_pagamento: "pendente" };

export default function AgendamentosPage() {
  const [items, setItems] = useState<Appointment[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [form, setForm] = useState(empty);
  const [editing, setEditing] = useState<number | null>(null);
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("todos");
  const [clientFilter, setClientFilter] = useState("todos");
  const [procedureFilter, setProcedureFilter] = useState("todos");

  async function load() {
    const [appointments, loadedClients, loadedProcedures, loadedProfessionals] = await Promise.all([
      apiGet<Appointment[]>("/agendamentos/"), apiGet<Client[]>("/clientes/"),
      apiGet<Procedure[]>("/procedimentos/"), apiGet<Professional[]>("/operacoes/profissionais"),
    ]);
    setItems(appointments); setClients(loadedClients); setProcedures(loadedProcedures); setProfessionals(loadedProfessionals);
  }
  useEffect(() => { load().catch((error) => setMessage(error instanceof Error ? error.message : "Não foi possível carregar agendamentos.")); }, []);
  useEffect(() => { if (!message) return; const timer = window.setTimeout(() => setMessage(null), 5000); return () => window.clearTimeout(timer); }, [message]);

  function start(item?: Appointment) {
    setEditing(item?.id ?? null);
    setForm(item ? {
      cliente_nome: clients.find((client) => client.id === item.cliente_id)?.nome ?? "",
      procedimento_id: String(item.procedimento_id), profissional_id: item.profissional_id == null ? "" : String(item.profissional_id),
      data_hora: item.data_hora.slice(0, 16), status: item.status,
      valor_cobrado: item.valor_cobrado == null ? "" : String(item.valor_cobrado),
      forma_pagamento: item.forma_pagamento ?? "", status_pagamento: item.status_pagamento ?? "pendente",
    } : empty);
    setOpen(true);
  }

  async function resolveClientId() {
    const name = form.cliente_nome.trim();
    const existing = clients.find((client) => client.nome.trim().localeCompare(name, "pt-BR", { sensitivity: "accent" }) === 0);
    if (existing?.id) return existing.id;
    const created = await apiPost<Client>("/clientes/", { nome: name });
    if (!created.id) throw new Error("Não foi possível identificar o cliente criado.");
    return created.id;
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      const payload = {
        cliente_id: await resolveClientId(), procedimento_id: Number(form.procedimento_id), profissional_id: Number(form.profissional_id),
        data_hora: `${form.data_hora}:00`, status: form.status,
        valor_cobrado: form.valor_cobrado === "" ? null : Number(form.valor_cobrado),
        forma_pagamento: form.forma_pagamento || null, status_pagamento: form.status_pagamento,
      };
      if (editing) await apiPut(`/agendamentos/${editing}`, payload); else await apiPost("/agendamentos/", payload);
      await load(); setOpen(false); setMessage("Agendamento salvo.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível salvar."); }
  }
  async function action(id: number, type: "confirmar" | "cancelar") {
    try { await apiPost(`/atendimento/agendamentos/${id}/${type}`); await load(); setMessage(type === "confirmar" ? "Agendamento confirmado." : "Agendamento cancelado."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Ação indisponível."); }
  }
  async function remove(id: number) {
    if (!window.confirm("Excluir este agendamento?")) return;
    try { await apiDelete(`/agendamentos/${id}`); await load(); setMessage("Agendamento excluído."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível excluir."); }
  }

  const rows = useMemo<AppointmentRow[]>(() => items.map((item) => ({
    ...item,
    cliente_nome: clients.find((client) => client.id === item.cliente_id)?.nome ?? "Cliente não encontrado",
    procedimento_nome: procedures.find((procedure) => procedure.id === item.procedimento_id)?.nome ?? "Procedimento não encontrado",
    profissional_nome: professionals.find((professional) => professional.id === item.profissional_id)?.nome ?? "Não definido",
  })), [items, clients, procedures, professionals]);
  const columns = useMemo<TableColumn<AppointmentRow>[]>(() => [
    { title: "Cliente", data: "cliente_nome" }, { title: "Procedimento", data: "procedimento_nome" }, { title: "Profissional", data: "profissional_nome" },
    { title: "Data e hora", data: "data_hora", render: (row) => new Date(row.data_hora).toLocaleString("pt-BR") },
    { title: "Status", data: "status", render: (row) => `<span class="status-pill status-${row.status}">${row.status}</span>` },
    { title: "Pagamento", data: "status_pagamento", render: (row) => row.status_pagamento || "pendente" },
    { title: "Ações", data: "id", render: (row) => `<button class="table-action table-edit" data-table-action="edit" data-id="${row.id}">Editar</button>${row.status === "pendente" ? `<button class="table-action table-confirm" data-table-action="confirm" data-id="${row.id}">Confirmar</button>` : ""}${!["cancelado", "concluido"].includes(row.status) ? `<button class="table-action table-delete" data-table-action="cancel" data-id="${row.id}">Cancelar</button>` : ""}<button class="table-action table-delete" data-table-action="delete" data-id="${row.id}">Excluir</button>` },
  ], []);
  const filtered = useMemo(() => rows.filter((row) => (statusFilter === "todos" || row.status === statusFilter) && (clientFilter === "todos" || String(row.cliente_id) === clientFilter) && (procedureFilter === "todos" || String(row.procedimento_id) === procedureFilter)), [rows, statusFilter, clientFilter, procedureFilter]);
  const paid = form.status_pagamento === "pago";
  function handleAction(name: string, id: number) { const item = items.find((entry) => entry.id === id); if (name === "edit" && item) start(item); if (name === "confirm") action(id, "confirmar"); if (name === "cancel") action(id, "cancelar"); if (name === "delete") remove(id); }
  function exportAppointments() { downloadCsv("agendamentos.csv", filtered.map((item) => ({ id: item.id ?? "", cliente: item.cliente_nome, procedimento: item.procedimento_nome, data: new Date(item.data_hora).toLocaleString("pt-BR"), status: item.status, valor: item.valor_cobrado ?? "", pagamento: item.forma_pagamento ?? "" }))); }

  return <div className="space-y-6">
    <header className="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between"><div><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Agendamentos</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Horários e confirmações</h1></div><div className="flex flex-wrap gap-2"><button onClick={exportAppointments} className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700"><Download size={16} /> CSV</button><button onClick={() => start()} className="inline-flex items-center justify-center gap-2 rounded-xl bg-fuchsia-700 px-4 py-2 text-sm font-medium text-white"><Plus size={16} /> Novo agendamento</button></div></header>
    {message && <p className="rounded-xl border border-fuchsia-200 bg-fuchsia-50 p-3 text-sm text-fuchsia-800">{message}</p>}
    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"><div className="mb-4 grid gap-2 md:grid-cols-3"><select className="field select-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="todos">Todos os status</option><option value="pendente">Pendente</option><option value="confirmado">Confirmado</option><option value="cancelado">Cancelado</option><option value="concluido">Concluído</option></select><select className="field select-field" value={clientFilter} onChange={(e) => setClientFilter(e.target.value)}><option value="todos">Todos os clientes</option>{clients.map((client) => <option key={client.id} value={client.id}>{client.nome}</option>)}</select><select className="field select-field" value={procedureFilter} onChange={(e) => setProcedureFilter(e.target.value)}><option value="todos">Todos os procedimentos</option>{procedures.map((procedure) => <option key={procedure.id} value={procedure.id}>{procedure.nome}</option>)}</select></div><InteractiveTable data={filtered} columns={columns} onAction={handleAction} /></section>
    {open && <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-950/40 p-4"><form onSubmit={save} className="my-4 w-full max-w-lg space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-xl"><div className="flex justify-between"><h2 className="text-xl font-semibold text-slate-900">{editing ? "Editar agendamento" : "Novo agendamento"}</h2><button type="button" aria-label="Fechar" onClick={() => setOpen(false)}><X /></button></div><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Cliente<input required list="clientes-agendamento" className="field mt-1" value={form.cliente_nome} onChange={(e) => setForm({ ...form, cliente_nome: e.target.value })} /><datalist id="clientes-agendamento">{clients.map((client) => <option key={client.id} value={client.nome} />)}</datalist></label><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Procedimento<select required className="field select-field mt-1" value={form.procedimento_id} onChange={(e) => setForm({ ...form, procedimento_id: e.target.value })}><option value="">Selecione o procedimento</option>{procedures.map((procedure) => <option key={procedure.id} value={procedure.id}>{procedure.nome} ({procedure.duracao} min)</option>)}</select></label><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Profissional<select required className="field select-field mt-1" value={form.profissional_id} onChange={(e) => setForm({ ...form, profissional_id: e.target.value })}><option value="">Selecione a profissional</option>{professionals.filter((professional) => professional.ativo || String(professional.id) === form.profissional_id).map((professional) => <option key={professional.id} value={professional.id}>{professional.nome}</option>)}</select></label><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Data e hora<input required type="datetime-local" className="field mt-1" value={form.data_hora} onChange={(e) => setForm({ ...form, data_hora: e.target.value })} /></label><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Status do atendimento<select className="field select-field mt-1" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}><option value="pendente">Pendente</option><option value="confirmado">Confirmado</option><option value="cancelado">Cancelado</option><option value="concluido">Concluído</option><option value="nao_compareceu">Não compareceu</option></select></label><fieldset className="space-y-3 rounded-xl border border-emerald-100 bg-emerald-50/50 p-4"><legend className="px-1 text-xs font-semibold uppercase tracking-wide text-emerald-800">Pagamento</legend><div className="grid gap-3 sm:grid-cols-2"><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Valor cobrado<input required={paid} min="0" step="0.01" type="number" inputMode="decimal" className="field mt-1" placeholder="0,00" value={form.valor_cobrado} onChange={(e) => setForm({ ...form, valor_cobrado: e.target.value })} /></label><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Forma de pagamento<select required={paid} className="field select-field mt-1" value={form.forma_pagamento} onChange={(e) => setForm({ ...form, forma_pagamento: e.target.value })}><option value="">Selecione a forma</option><option value="pix">PIX</option><option value="dinheiro">Dinheiro</option><option value="credito">Cartão de crédito</option><option value="debito">Cartão de débito</option><option value="misto">Misto</option><option value="parceria">Parceria</option><option value="cortesia">Cortesia</option></select></label></div><label className="block text-xs font-semibold uppercase tracking-wide text-slate-500">Status do pagamento<select className="field select-field mt-1" value={form.status_pagamento} onChange={(e) => setForm({ ...form, status_pagamento: e.target.value })}><option value="pendente">Pendente</option><option value="pago">Pago</option></select></label></fieldset><button className="w-full rounded-xl bg-fuchsia-700 px-4 py-3 font-medium text-white">Salvar</button></form></div>}
  </div>;
}
