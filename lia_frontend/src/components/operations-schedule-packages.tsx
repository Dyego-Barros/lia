"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { CalendarClock, PackagePlus, Trash2 } from "lucide-react";
import { apiDelete, apiGet, apiPost } from "@/lib/api";

type Professional = { id?: number; nome: string; ativo: boolean };
type Schedule = { id: number; profissional_id: number; weekday: number; inicio: string; fim: string };
type Procedure = { id?: number; nome: string; duracao: number };
type PackageItem = { id: number; procedimento_id: number; procedimento_nome: string; quantidade: number };
type ServicePackage = { id: number; nome: string; descricao?: string | null; preco: number; ativo: boolean; procedimentos: PackageItem[] };

const weekdays = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"];

function time(value: string) { return value.slice(0, 5); }

export function OperationsSchedulePackages({ professionals }: { professionals: Professional[] }) {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [packages, setPackages] = useState<ServicePackage[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [scheduleForm, setScheduleForm] = useState({ profissional_id: "", weekday: "0", inicio: "08:00", fim: "18:00" });
  const [packageForm, setPackageForm] = useState({ nome: "", descricao: "", preco: "" });
  const [itemForms, setItemForms] = useState<Record<number, { procedimento_id: string; quantidade: string }>>({});

  const activeProfessionals = useMemo(() => professionals.filter((professional) => professional.ativo && professional.id), [professionals]);
  async function load() {
    const [scheduleResult, packageResult, procedureResult] = await Promise.allSettled([
      apiGet<Schedule[]>("/operacoes/horarios"), apiGet<ServicePackage[]>("/operacoes/pacotes"), apiGet<Procedure[]>("/procedimentos/"),
    ]);
    if (scheduleResult.status === "fulfilled") setSchedules(scheduleResult.value);
    if (packageResult.status === "fulfilled") setPackages(packageResult.value);
    if (procedureResult.status === "fulfilled") setProcedures(procedureResult.value);
    const failure = [scheduleResult, packageResult, procedureResult].find((result) => result.status === "rejected");
    if (failure?.status === "rejected") setMessage(failure.reason instanceof Error ? failure.reason.message : "Não foi possível carregar configurações.");
  }
  useEffect(() => { void load(); }, []);
  useEffect(() => { if (!message) return; const timer = window.setTimeout(() => setMessage(null), 5000); return () => window.clearTimeout(timer); }, [message]);

  async function saveSchedule(event: FormEvent) {
    event.preventDefault();
    try {
      await apiPost("/operacoes/horarios", { ...scheduleForm, profissional_id: Number(scheduleForm.profissional_id), weekday: Number(scheduleForm.weekday), inicio: `${scheduleForm.inicio}:00`, fim: `${scheduleForm.fim}:00` });
      await load(); setMessage("Horário de atendimento adicionado.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível adicionar o horário."); }
  }
  async function deleteSchedule(id: number) {
    if (!window.confirm("Remover este período de atendimento?")) return;
    try { await apiDelete(`/operacoes/horarios/${id}`); await load(); setMessage("Horário removido."); } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível remover o horário."); }
  }
  async function savePackage(event: FormEvent) {
    event.preventDefault();
    try {
      await apiPost("/operacoes/pacotes", { ...packageForm, preco: Number(packageForm.preco), ativo: true });
      setPackageForm({ nome: "", descricao: "", preco: "" }); await load(); setMessage("Pacote criado. Agora adicione os procedimentos inclusos.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível criar o pacote."); }
  }
  async function deletePackage(id: number) {
    if (!window.confirm("Excluir este pacote e seus procedimentos?")) return;
    try { await apiDelete(`/operacoes/pacotes/${id}`); await load(); setMessage("Pacote removido."); } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível remover o pacote."); }
  }
  async function addPackageItem(event: FormEvent, pacoteId: number) {
    event.preventDefault(); const form = itemForms[pacoteId]; if (!form?.procedimento_id) return;
    try {
      await apiPost("/operacoes/pacotes/procedimentos", { pacote_id: pacoteId, procedimento_id: Number(form.procedimento_id), quantidade: Number(form.quantidade || "1") });
      setItemForms({ ...itemForms, [pacoteId]: { procedimento_id: "", quantidade: "1" } }); await load(); setMessage("Procedimento adicionado ao pacote.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível adicionar o procedimento."); }
  }
  async function deletePackageItem(id: number) {
    try { await apiDelete(`/operacoes/pacotes/procedimentos/${id}`); await load(); setMessage("Procedimento removido do pacote."); } catch (error) { setMessage(error instanceof Error ? error.message : "Não foi possível remover o procedimento."); }
  }

  return <section className="space-y-4">{message && <p className="rounded-xl border border-fuchsia-200 bg-fuchsia-50 p-3 text-sm text-fuchsia-800">{message}</p>}<div className="grid gap-4 xl:grid-cols-2"><form onSubmit={saveSchedule} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><CalendarClock size={18} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Horários das profissionais</h2></div><p className="text-sm text-slate-500">Cadastre turnos semanais. Você pode criar, por exemplo, 08:00–12:00 e 13:00–18:00 no mesmo dia.</p><select required className="field select-field" value={scheduleForm.profissional_id} onChange={(event) => setScheduleForm({ ...scheduleForm, profissional_id: event.target.value })}><option value="">Selecione a profissional</option>{activeProfessionals.map((professional) => <option key={professional.id} value={professional.id}>{professional.nome}</option>)}</select><div className="grid grid-cols-3 gap-2"><select className="field select-field" value={scheduleForm.weekday} onChange={(event) => setScheduleForm({ ...scheduleForm, weekday: event.target.value })}>{weekdays.map((day, index) => <option key={day} value={index}>{day}</option>)}</select><input required type="time" className="field" value={scheduleForm.inicio} onChange={(event) => setScheduleForm({ ...scheduleForm, inicio: event.target.value })} /><input required type="time" className="field" value={scheduleForm.fim} onChange={(event) => setScheduleForm({ ...scheduleForm, fim: event.target.value })} /></div><button className="primary-button"><CalendarClock size={16} />Adicionar período</button></form><div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="mb-3 text-lg font-semibold text-slate-900">Escala cadastrada</h2>{schedules.length ? <div className="space-y-2">{schedules.map((schedule) => <div key={schedule.id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 p-3 text-sm"><span><strong>{professionals.find((professional) => professional.id === schedule.profissional_id)?.nome ?? `Profissional #${schedule.profissional_id}`}</strong> · {weekdays[schedule.weekday]} · {time(schedule.inicio)}–{time(schedule.fim)}</span><button type="button" aria-label="Remover horário" onClick={() => deleteSchedule(schedule.id)} className="text-rose-600"><Trash2 size={17} /></button></div>)}</div> : <p className="text-sm text-slate-400">Nenhum horário cadastrado. Sem escala, a profissional não será oferecida pela agenda.</p>}</div></div><div className="grid gap-4 xl:grid-cols-2"><form onSubmit={savePackage} className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center gap-2"><PackagePlus size={18} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Novo pacote</h2></div><input required minLength={2} className="field" placeholder="Nome do pacote" value={packageForm.nome} onChange={(event) => setPackageForm({ ...packageForm, nome: event.target.value })} /><textarea className="field min-h-20" placeholder="Descrição (opcional)" value={packageForm.descricao} onChange={(event) => setPackageForm({ ...packageForm, descricao: event.target.value })} /><input required min="0" step="0.01" type="number" className="field" placeholder="Preço total" value={packageForm.preco} onChange={(event) => setPackageForm({ ...packageForm, preco: event.target.value })} /><button className="primary-button"><PackagePlus size={16} />Criar pacote</button></form><div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="mb-3 text-lg font-semibold text-slate-900">Pacotes cadastrados</h2>{packages.length ? <div className="space-y-3">{packages.map((item) => <div key={item.id} className="rounded-xl border border-slate-100 p-4"><div className="flex justify-between gap-2"><div><h3 className="font-semibold text-slate-900">{item.nome} · R$ {item.preco.toFixed(2)}</h3>{item.descricao && <p className="mt-1 text-sm text-slate-500">{item.descricao}</p>}</div><button type="button" aria-label="Excluir pacote" onClick={() => deletePackage(item.id)} className="text-rose-600"><Trash2 size={17} /></button></div><ul className="mt-3 space-y-1 text-sm text-slate-600">{item.procedimentos.map((procedure) => <li key={procedure.id} className="flex justify-between"><span>{procedure.quantidade}× {procedure.procedimento_nome}</span><button type="button" onClick={() => deletePackageItem(procedure.id)} className="text-rose-600">remover</button></li>)}{!item.procedimentos.length && <li className="text-slate-400">Nenhum procedimento incluso.</li>}</ul><form onSubmit={(event) => addPackageItem(event, item.id)} className="mt-3 grid grid-cols-[1fr_70px_auto] gap-2"><select required className="field select-field" value={itemForms[item.id]?.procedimento_id ?? ""} onChange={(event) => setItemForms({ ...itemForms, [item.id]: { procedimento_id: event.target.value, quantidade: itemForms[item.id]?.quantidade ?? "1" } })}><option value="">Adicionar procedimento</option>{procedures.map((procedure) => <option key={procedure.id} value={procedure.id}>{procedure.nome}</option>)}</select><input required min="1" type="number" className="field" value={itemForms[item.id]?.quantidade ?? "1"} onChange={(event) => setItemForms({ ...itemForms, [item.id]: { procedimento_id: itemForms[item.id]?.procedimento_id ?? "", quantidade: event.target.value } })} /><button className="rounded-xl bg-slate-900 px-3 text-sm font-medium text-white">Adicionar</button></form></div>)}</div> : <p className="text-sm text-slate-400">Nenhum pacote cadastrado.</p>}</div></div></section>;
}
