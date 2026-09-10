"use client";

import { FormEvent, Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Boxes, CalendarOff, Clock3, CreditCard, Package, Plus, Star, UsersRound } from "lucide-react";
import { InteractiveTable } from "@/components/interactive-table-lazy";
import type { TableColumn } from "@/components/interactive-table";
import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "@/lib/api";
import { OperationsSchedulePackages } from "@/components/operations-schedule-packages";

type Professional = { id?: number; nome: string; especialidade?: string | null; email?: string | null; ativo: boolean };
type Block = { id?: number; inicio: string; fim: string; motivo: string; profissional_id?: number | null };
type WaitItem = { id?: number; cliente_id: number; procedimento_id: number; data_preferida?: string | null; status: string };
type Payment = { id?: number; agendamento_id: number; cliente_nome: string; procedimento_nome: string; data_hora: string; valor: number; forma: string; status: string; pago_em: string };
type Stock = { id?: number; nome: string; sku?: string | null; quantidade: number; estoque_minimo: number; custo_unitario: number };
type ProcedureMini = { id?: number; nome: string };
type MaterialLink = { id: number; procedimento_id: number; procedimento_nome: string; produto_id: number; produto_nome: string; quantidade: number };
type User = { id?: number; nome: string; email: string; role: string; ativo: boolean };
const input = { nome: "", especialidade: "", email: "", ativo: true };
const operationSections = ["equipe", "pacotes", "pagamentos", "estoque", "espera", "usuarios"] as const;
type OperationSection = (typeof operationSections)[number];

export default function OperacoesPage() {
  return <Suspense fallback={<div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Carregando operações...</div>}><OperationsContent /></Suspense>;
}

function OperationsContent() {
  const searchParams = useSearchParams();
  const requestedSection = searchParams.get("secao");
  const section: OperationSection = operationSections.includes(requestedSection as OperationSection) ? requestedSection as OperationSection : "equipe";
  const [professionals, setProfessionals] = useState<Professional[]>([]); const [blocks, setBlocks] = useState<Block[]>([]); const [waitlist, setWaitlist] = useState<WaitItem[]>([]); const [payments, setPayments] = useState<Payment[]>([]); const [stock, setStock] = useState<Stock[]>([]); const [users, setUsers] = useState<User[]>([]); const [professionalForm, setProfessionalForm] = useState(input); const [blockForm, setBlockForm] = useState({ inicio: "", fim: "", motivo: "" }); const [stockForm, setStockForm] = useState({ nome: "", sku: "", quantidade: "0", estoque_minimo: "0", custo_unitario: "0" }); const [editingStockId, setEditingStockId] = useState<number | null>(null); const [message, setMessage] = useState<string | null>(null);
  const [procedures, setProcedures] = useState<ProcedureMini[]>([]); const [materialLinks, setMaterialLinks] = useState<MaterialLink[]>([]); const [materialForm, setMaterialForm] = useState({ procedimento_id: "", produto_id: "", quantidade: "1" });
  useEffect(() => { if (!message) return; const timer = window.setTimeout(() => setMessage(null), 5000); return () => window.clearTimeout(timer); }, [message]);
  async function load() { const results = await Promise.allSettled([apiGet<Professional[]>("/operacoes/profissionais"), apiGet<Block[]>("/operacoes/bloqueios"), apiGet<WaitItem[]>("/operacoes/lista-espera"), apiGet<Payment[]>("/operacoes/pagamentos"), apiGet<Stock[]>("/operacoes/estoque/produtos"), apiGet<User[]>("/operacoes/usuarios")]); if (results[0].status === "fulfilled") setProfessionals(results[0].value); if (results[1].status === "fulfilled") setBlocks(results[1].value); if (results[2].status === "fulfilled") setWaitlist(results[2].value); if (results[3].status === "fulfilled") setPayments(results[3].value); if (results[4].status === "fulfilled") setStock(results[4].value); if (results[5].status === "fulfilled") setUsers(results[5].value); const failed = results.find((result) => result.status === "rejected"); if (failed?.status === "rejected") setMessage(failed.reason instanceof Error ? failed.reason.message : "Falha ao carregar operações."); }
  useEffect(() => { Promise.resolve().then(() => load()).then(() => setMessage(null)).catch((e) => console.error("Falha ao carregar operações", e)); }, []);
  async function loadMaterialLinks() { const [p, links] = await Promise.all([apiGet<ProcedureMini[]>("/procedimentos/"), apiGet<MaterialLink[]>("/operacoes/estoque/vinculos")]); setProcedures(p); setMaterialLinks(links); }
  useEffect(() => { Promise.resolve().then(() => loadMaterialLinks()).catch((e) => console.error("Falha ao carregar vínculos de materiais", e)); }, []);
  async function submitProfessional(e: FormEvent) { e.preventDefault(); try { await apiPost("/operacoes/profissionais", professionalForm); setProfessionalForm(input); await load(); setMessage("Profissional cadastrado."); } catch (e) { setMessage(e instanceof Error ? e.message : "Erro ao cadastrar profissional."); } }
  async function submitBlock(e: FormEvent) { e.preventDefault(); try { await apiPost("/operacoes/bloqueios", { ...blockForm, inicio: `${blockForm.inicio}:00`, fim: `${blockForm.fim}:00` }); setBlockForm({ inicio: "", fim: "", motivo: "" }); await load(); setMessage("Bloqueio criado."); } catch (e) { setMessage(e instanceof Error ? e.message : "Erro ao criar bloqueio."); } }
  async function submitStock(e: FormEvent) { e.preventDefault(); try { const payload = { ...stockForm, quantidade: Number(stockForm.quantidade), estoque_minimo: Number(stockForm.estoque_minimo), custo_unitario: Number(stockForm.custo_unitario), ativo: true }; if (editingStockId) await apiPut(`/operacoes/estoque/produtos/${editingStockId}`, payload); else await apiPost("/operacoes/estoque/produtos", payload); setStockForm({ nome: "", sku: "", quantidade: "0", estoque_minimo: "0", custo_unitario: "0" }); setEditingStockId(null); await load(); setMessage(editingStockId ? "Produto atualizado." : "Produto adicionado ao estoque."); } catch (e) { setMessage(e instanceof Error ? e.message : "Erro ao salvar produto."); } }
  function editStock(item: Stock) { if (!item.id) return; setEditingStockId(item.id); setStockForm({ nome: item.nome, sku: item.sku ?? "", quantidade: String(item.quantidade), estoque_minimo: String(item.estoque_minimo), custo_unitario: String(item.custo_unitario) }); window.scrollTo({ top: 0, behavior: "smooth" }); }
  async function stockAction(action: string, id: number) { const item = stock.find((entry) => entry.id === id); if (!item) return; if (action === "edit") { editStock(item); return; } if (action !== "delete" || !window.confirm(`Excluir o produto “${item.nome}”?`)) return; try { await apiDelete(`/operacoes/estoque/produtos/${id}`); if (editingStockId === id) { setEditingStockId(null); setStockForm({ nome: "", sku: "", quantidade: "0", estoque_minimo: "0", custo_unitario: "0" }); } await load(); setMessage("Produto excluído."); } catch (e) { setMessage(e instanceof Error ? e.message : "Erro ao excluir produto."); } }
  async function submitMaterialLink(e: FormEvent) { e.preventDefault(); try { await apiPost("/operacoes/estoque/vinculos", { procedimento_id: Number(materialForm.procedimento_id), produto_id: Number(materialForm.produto_id), quantidade: Number(materialForm.quantidade) }); setMaterialForm({ procedimento_id: "", produto_id: "", quantidade: "1" }); await loadMaterialLinks(); setMessage("Material vinculado ao procedimento."); } catch (e) { setMessage(e instanceof Error ? e.message : "Erro ao vincular material."); } }
  async function deleteMaterialLink(id: number) { if (!window.confirm("Remover este material do procedimento?")) return; try { await apiDelete(`/operacoes/estoque/vinculos/${id}`); await loadMaterialLinks(); setMessage("Vínculo removido."); } catch (e) { setMessage(e instanceof Error ? e.message : "Erro ao remover vínculo."); } }
  async function professionalAction(action: string, id: number) { const item = professionals.find((entry) => entry.id === id); if (!item) return; try { if (action === "toggle") await apiPatch(`/operacoes/profissionais/${id}/status?ativo=${!item.ativo}`, {}); if (action === "delete") { if (!window.confirm("Excluir ou desativar este profissional?")) return; await apiDelete(`/operacoes/profissionais/${id}`); } await load(); setMessage(action === "toggle" ? "Status do profissional atualizado." : "Profissional removido ou desativado."); } catch (e) { setMessage(e instanceof Error ? e.message : "Falha na operação do profissional."); } }
  async function waitAction(action: string, id: number) { try { if (action === "delete") await apiDelete(`/operacoes/lista-espera/${id}`); if (action === "cancel") await apiPatch(`/operacoes/lista-espera/${id}`, { status: "cancelado" }); if (action === "promote") { const value = window.prompt("Data e hora (YYYY-MM-DDTHH:mm):"); if (!value) return; await apiPost(`/operacoes/lista-espera/${id}/promover`, { data_hora: `${value}:00` }); } await load(); setMessage("Lista de espera atualizada."); } catch (e) { setMessage(e instanceof Error ? e.message : "Falha na operação da lista de espera."); } }
  const professionalColumns = useMemo<TableColumn<Professional>[]>(() => [{ title: "Nome", data: "nome" }, { title: "Especialidade", data: "especialidade", render: (row) => row.especialidade || "—" }, { title: "E-mail", data: "email", render: (row) => row.email || "—" }, { title: "Status", data: "ativo", render: (row) => row.ativo ? "Ativo" : "Inativo" }, { title: "Ações", data: "id", render: (row) => `<button class="table-action table-edit" data-table-action="toggle" data-id="${row.id}">${row.ativo ? "Desativar" : "Ativar"}</button><button class="table-action table-delete" data-table-action="delete" data-id="${row.id}">Excluir</button>` }], []);
  const blockColumns = useMemo<TableColumn<Block>[]>(() => [{ title: "Início", data: "inicio", render: (row) => new Date(row.inicio).toLocaleString("pt-BR") }, { title: "Fim", data: "fim", render: (row) => new Date(row.fim).toLocaleString("pt-BR") }, { title: "Motivo", data: "motivo" }], []);
  const paymentColumns = useMemo<TableColumn<Payment>[]>(() => [{ title: "Cliente", data: "cliente_nome" }, { title: "Procedimento", data: "procedimento_nome" }, { title: "Data", data: "data_hora", render: (row) => new Date(row.data_hora).toLocaleString("pt-BR") }, { title: "Valor", data: "valor", render: (row) => `R$ ${row.valor.toFixed(2)}` }, { title: "Forma", data: "forma" }, { title: "Status", data: "status" }], []);
  const stockColumns = useMemo<TableColumn<Stock>[]>(() => [{ title: "Produto", data: "nome" }, { title: "SKU", data: "sku", render: (row) => row.sku || "—" }, { title: "Quantidade", data: "quantidade" }, { title: "Mínimo", data: "estoque_minimo" }, { title: "Custo", data: "custo_unitario", render: (row) => `R$ ${row.custo_unitario.toFixed(2)}` }, { title: "Ações", data: "id", render: (row) => `<button class="table-action table-edit" data-table-action="edit" data-id="${row.id}">Editar</button><button class="table-action table-delete" data-table-action="delete" data-id="${row.id}">Excluir</button>` }], []);
  return (
    <div className="space-y-6">
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">Mayssa · Operações</p>
        <h1 className="mt-2 text-2xl font-semibold text-slate-900">Gestão do negócio</h1>
        <p className="mt-2 text-sm text-slate-500">Use o submenu Operações para alternar entre as áreas administrativas.</p>
      </header>
      {message && <p className="rounded-xl border border-fuchsia-200 bg-fuchsia-50 p-3 text-sm text-fuchsia-800">{message}</p>}

      {section === "equipe" && <>
        <div className="grid gap-4 lg:grid-cols-2">
          <FormCard title="Novo profissional" icon={<UsersRound size={18} />} onSubmit={submitProfessional}>
            <input required minLength={3} className="field" placeholder="Nome" value={professionalForm.nome} onChange={(e) => setProfessionalForm({ ...professionalForm, nome: e.target.value })} />
            <input className="field" placeholder="Especialidade" value={professionalForm.especialidade} onChange={(e) => setProfessionalForm({ ...professionalForm, especialidade: e.target.value })} />
            <input type="email" className="field" placeholder="E-mail" value={professionalForm.email} onChange={(e) => setProfessionalForm({ ...professionalForm, email: e.target.value })} />
            <button className="primary-button"><Plus size={16} />Cadastrar</button>
          </FormCard>
          <FormCard title="Bloquear agenda" icon={<CalendarOff size={18} />} onSubmit={submitBlock}>
            <input required type="datetime-local" className="field" value={blockForm.inicio} onChange={(e) => setBlockForm({ ...blockForm, inicio: e.target.value })} />
            <input required type="datetime-local" className="field" value={blockForm.fim} onChange={(e) => setBlockForm({ ...blockForm, fim: e.target.value })} />
            <input required className="field" placeholder="Motivo" value={blockForm.motivo} onChange={(e) => setBlockForm({ ...blockForm, motivo: e.target.value })} />
            <button className="primary-button"><CalendarOff size={16} />Criar bloqueio</button>
          </FormCard>
        </div>
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2"><UsersRound size={18} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Profissionais</h2></div>
          <InteractiveTable data={professionals} columns={professionalColumns} onAction={professionalAction} />
        </section>
        <OperationsSchedulePackages professionals={professionals} view="schedule" />
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2"><Clock3 size={18} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Bloqueios de agenda</h2></div>
          <InteractiveTable data={blocks} columns={blockColumns} />
        </section>
      </>}

      {section === "pacotes" && <OperationsSchedulePackages professionals={professionals} view="packages" />}

      {section === "pagamentos" && <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4 flex items-center gap-2"><CreditCard size={18} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Pagamentos</h2></div>
        <InteractiveTable data={payments} columns={paymentColumns} />
      </section>}

      {section === "estoque" && <>
        <FormCard title={editingStockId ? "Editar produto do estoque" : "Novo produto no estoque"} icon={<Boxes size={18} />} onSubmit={submitStock}>
          <input required className="field" placeholder="Nome do produto" value={stockForm.nome} onChange={(e) => setStockForm({ ...stockForm, nome: e.target.value })} />
          <input className="field" placeholder="SKU" value={stockForm.sku} onChange={(e) => setStockForm({ ...stockForm, sku: e.target.value })} />
          <div className="grid grid-cols-3 gap-2">
            <input type="number" min="0" step="0.001" className="field" placeholder="Qtd." value={stockForm.quantidade} onChange={(e) => setStockForm({ ...stockForm, quantidade: e.target.value })} />
            <input type="number" min="0" className="field" placeholder="Mínimo" value={stockForm.estoque_minimo} onChange={(e) => setStockForm({ ...stockForm, estoque_minimo: e.target.value })} />
            <input type="number" min="0" step="0.01" className="field" placeholder="Custo" value={stockForm.custo_unitario} onChange={(e) => setStockForm({ ...stockForm, custo_unitario: e.target.value })} />
          </div>
          <div className="flex gap-2"><button className="primary-button flex-1"><Package size={16} />{editingStockId ? "Salvar alterações" : "Adicionar produto"}</button>{editingStockId && <button type="button" className="rounded-xl border border-slate-200 px-4 text-sm font-medium text-slate-600" onClick={() => { setEditingStockId(null); setStockForm({ nome: "", sku: "", quantidade: "0", estoque_minimo: "0", custo_unitario: "0" }); }}>Cancelar</button>}</div>
        </FormCard>
        <FormCard title="Materiais usados por procedimento" icon={<Package size={18} />} onSubmit={submitMaterialLink}>
          <select required className="field select-field" value={materialForm.procedimento_id} onChange={(e) => setMaterialForm({ ...materialForm, procedimento_id: e.target.value })}><option value="">Selecione o procedimento</option>{procedures.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}</select>
          <select required className="field select-field" value={materialForm.produto_id} onChange={(e) => setMaterialForm({ ...materialForm, produto_id: e.target.value })}><option value="">Selecione o produto</option>{stock.map((item) => <option key={item.id} value={item.id}>{item.nome}</option>)}</select>
          <input required type="number" min="0.001" step="0.001" className="field" placeholder="Quantidade consumida por atendimento" value={materialForm.quantidade} onChange={(e) => setMaterialForm({ ...materialForm, quantidade: e.target.value })} />
          <button className="primary-button"><Plus size={16} />Vincular material</button>
          <div className="space-y-2">{materialLinks.map((item) => <div key={item.id} className="flex items-center justify-between rounded-lg bg-slate-50 p-3 text-sm"><span><strong>{item.procedimento_nome}</strong> · {item.quantidade} × {item.produto_nome}</span><button type="button" className="table-action table-delete" onClick={() => deleteMaterialLink(item.id)}>Excluir</button></div>)}</div>
        </FormCard>
        <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center gap-2"><Package size={18} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Estoque</h2></div>
          <InteractiveTable data={stock} columns={stockColumns} onAction={stockAction} />
        </section>
      </>}

      {section === "espera" && <>
        <WaitList items={waitlist} onAction={waitAction} />
        <div className="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-500 shadow-sm"><Star className="mb-2 text-amber-500" size={18} />Ações de promoção e cancelamento da lista de espera estão disponíveis diretamente nesta tela.</div>
      </>}

      {section === "usuarios" && <DataList title="Usuários cadastrados" icon={<UsersRound size={18} />} items={users.map((user) => `${user.nome} · ${user.email} · ${user.role}`)} />}
    </div>
  );
}

function FormCard({ title, icon, children, onSubmit }: { title: string; icon: React.ReactNode; children: React.ReactNode; onSubmit: (event: FormEvent) => void }) { return <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-2 flex items-center gap-2 text-slate-900">{icon}<h2 className="font-semibold">{title}</h2></div>{children}</form>; }
function DataList({ title, icon, items }: { title: string; icon: React.ReactNode; items: string[] }) { return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-3 flex items-center gap-2 text-slate-900">{icon}<h2 className="font-semibold">{title}</h2></div>{items.length ? <div className="space-y-2 text-sm text-slate-600">{items.map((item, index) => <p key={`${item}-${index}`} className="rounded-lg bg-slate-50 p-3">{item}</p>)}</div> : <p className="text-sm text-slate-400">Nenhum registro.</p>}</section>; }
function WaitList({ items, onAction }: { items: WaitItem[]; onAction: (action: string, id: number) => void }) { return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-3 flex items-center gap-2 text-slate-900"><Clock3 size={18} /><h2 className="font-semibold">Lista de espera</h2></div>{items.length ? <div className="space-y-2 text-sm text-slate-600">{items.map((item) => <div key={item.id} className="flex items-center justify-between gap-2 rounded-lg bg-slate-50 p-3"><span>Cliente #{item.cliente_id} · Procedimento #{item.procedimento_id}<br /><small>{item.status}</small></span>{(item.status === "aguardando" || item.status === "notificado") && <span className="flex gap-1"><button onClick={() => onAction("promote", item.id!)} className="table-action table-confirm">Promover</button><button onClick={() => onAction("cancel", item.id!)} className="table-action table-delete">Cancelar</button></span>}<button onClick={() => onAction("delete", item.id!)} className="table-action table-delete">Excluir</button></div>)}</div> : <p className="text-sm text-slate-400">Nenhum registro.</p>}</section>; }
