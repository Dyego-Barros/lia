"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Activity, AlertTriangle, ArrowDownRight, ArrowRight, ArrowUpRight, CalendarClock, CalendarDays, CalendarPlus, CircleDollarSign, CreditCard, MessageSquareText, UserCheck, UserPlus, Users } from "lucide-react";
import { apiGet } from "@/lib/api";
import { ContactAvatar } from "@/components/contact-avatar";

type DailyReport = { agendamentos: number; clientes_do_dia: number; faturamento: number };
type Appointment = { id?: number; cliente_id: number; procedimento_id: number; profissional_id?: number | null; data_hora: string; status: string; valor_cobrado?: number | null; status_pagamento?: string };
type Client = { id?: number; nome: string };
type Procedure = { id?: number; nome: string; duracao: number; preco: number };
type Professional = { id?: number; nome: string; ativo: boolean };
type Schedule = { id: number; profissional_id: number; weekday: number; inicio: string; fim: string };
type Conversation = { id: string; telefone: string; nome_contato: string | null; foto_perfil?: string | null; ultima_mensagem_recebida?: { conteudo: string; enviado_em: string } | null };

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const statusLabels: Record<string, string> = { pendente: "Pendentes", confirmado: "Confirmados", concluido: "Concluídos", cancelado: "Cancelados", nao_compareceu: "Não compareceram" };
const statusHex: Record<string, string> = { pendente: "#f59e0b", confirmado: "#6366f1", concluido: "#10b981", cancelado: "#f43f5e", nao_compareceu: "#64748b" };

function isoDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function minutes(time: string) {
  const [hour, minute] = time.slice(0, 5).split(":").map(Number);
  return hour * 60 + minute;
}

function variation(current: number, previous: number) {
  if (!previous) return current ? 100 : 0;
  return ((current - previous) / previous) * 100;
}

export default function DashboardPage() {
  const [report, setReport] = useState<DailyReport | null>(null);
  const [yesterdayReport, setYesterdayReport] = useState<DailyReport | null>(null);
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [professionals, setProfessionals] = useState<Professional[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const now = new Date();
    const today = isoDate(now);
    const yesterday = isoDate(new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1));
    Promise.allSettled([
      apiGet<DailyReport>(`/relatorios/resumo?inicio=${today}&fim=${today}`),
      apiGet<DailyReport>(`/relatorios/resumo?inicio=${yesterday}&fim=${yesterday}`),
      apiGet<Appointment[]>("/agendamentos/"),
      apiGet<Client[]>("/clientes/"),
      apiGet<Procedure[]>("/procedimentos/"),
      apiGet<Professional[]>("/operacoes/profissionais"),
      apiGet<Schedule[]>("/operacoes/horarios"),
      apiGet<Conversation[]>("/integracoes/conversas"),
    ]).then(([daily, previous, agenda, customerList, procedureList, team, workHours, inbox]) => {
      if (daily.status === "fulfilled") setReport(daily.value); else setError("Não foi possível carregar o resumo do dia.");
      if (previous.status === "fulfilled") setYesterdayReport(previous.value);
      if (agenda.status === "fulfilled") setAppointments(agenda.value);
      if (customerList.status === "fulfilled") setClients(customerList.value);
      if (procedureList.status === "fulfilled") setProcedures(procedureList.value);
      if (team.status === "fulfilled") setProfessionals(team.value);
      if (workHours.status === "fulfilled") setSchedules(workHours.value);
      if (inbox.status === "fulfilled") setConversations(inbox.value.filter((item) => item.ultima_mensagem_recebida).slice(0, 5));
    });
  }, []);

  const clientNames = useMemo(() => new Map(clients.flatMap((item) => item.id ? [[item.id, item.nome] as const] : [])), [clients]);
  const procedureMap = useMemo(() => new Map(procedures.flatMap((item) => item.id ? [[item.id, item] as const] : [])), [procedures]);
  const professionalNames = useMemo(() => new Map(professionals.flatMap((item) => item.id ? [[item.id, item.nome] as const] : [])), [professionals]);
  const now = new Date();
  const todayKey = isoDate(now);
  const monthKey = todayKey.slice(0, 7);
  const scheduleWeekday = (now.getDay() + 6) % 7;
  const todayAppointments = appointments.filter((item) => item.data_hora.slice(0, 10) === todayKey && item.status !== "cancelado");
  const upcoming = todayAppointments.filter((item) => new Date(item.data_hora) >= now && !["concluido", "nao_compareceu"].includes(item.status)).sort((a, b) => a.data_hora.localeCompare(b.data_hora)).slice(0, 5);
  const pendingPayments = todayAppointments.filter((item) => item.status_pagamento !== "pago");
  const expectedPending = pendingPayments.reduce((sum, item) => sum + (item.valor_cobrado ?? procedureMap.get(item.procedimento_id)?.preco ?? 0), 0);
  const statusCounts = Object.entries(todayAppointments.reduce<Record<string, number>>((totals, item) => ({ ...totals, [item.status]: (totals[item.status] ?? 0) + 1 }), {}));
  const statusTotal = statusCounts.reduce((sum, [, count]) => sum + count, 0);
  let statusCursor = 0;
  const statusSegments = statusCounts.map(([status, count]) => {
    const start = statusCursor;
    statusCursor += statusTotal ? (count / statusTotal) * 100 : 0;
    return `${statusHex[status] ?? "#64748b"} ${start}% ${statusCursor}%`;
  });
  const statusBackground = statusTotal ? `conic-gradient(${statusSegments.join(", ")})` : "conic-gradient(#e2e8f0 0 100%)";

  const occupancy = professionals.filter((item) => item.ativo && item.id).map((professional) => {
    const capacity = schedules.filter((item) => item.profissional_id === professional.id && item.weekday === scheduleWeekday).reduce((sum, item) => sum + Math.max(minutes(item.fim) - minutes(item.inicio), 0), 0);
    const ownAppointments = todayAppointments.filter((item) => item.profissional_id === professional.id);
    const booked = ownAppointments.reduce((sum, item) => sum + (procedureMap.get(item.procedimento_id)?.duracao ?? 0), 0);
    const next = ownAppointments.filter((item) => new Date(item.data_hora) >= now).sort((a, b) => a.data_hora.localeCompare(b.data_hora))[0];
    return { id: professional.id!, name: professional.nome, count: ownAppointments.length, booked, capacity, percentage: capacity ? Math.min((booked / capacity) * 100, 100) : booked ? 100 : 0, next };
  });
  const totalBookedMinutes = occupancy.reduce((sum, item) => sum + item.booked, 0);
  const totalCapacityMinutes = occupancy.reduce((sum, item) => sum + item.capacity, 0);
  const occupancyPercentage = totalCapacityMinutes ? Math.min((totalBookedMinutes / totalCapacityMinutes) * 100, 100) : totalBookedMinutes ? 100 : 0;

  const topProcedures = Object.entries(appointments.filter((item) => item.data_hora.slice(0, 7) === monthKey && item.status !== "cancelado").reduce<Record<number, number>>((totals, item) => ({ ...totals, [item.procedimento_id]: (totals[item.procedimento_id] ?? 0) + 1 }), {})).map(([id, count]) => ({ id: Number(id), count })).sort((a, b) => b.count - a.count).slice(0, 5);
  const maximumProcedure = Math.max(...topProcedures.map((item) => item.count), 1);
  const pendingConfirmation = todayAppointments.filter((item) => item.status === "pendente").length;
  const withoutProfessional = todayAppointments.filter((item) => !item.profissional_id).length;

  const cards = [
    { title: "Procedimentos do dia", value: report?.agendamentos ?? 0, hint: "agendados hoje", icon: Activity, cardClass: "border-fuchsia-200 bg-gradient-to-br from-fuchsia-50 to-white", titleClass: "text-fuchsia-800", iconClass: "bg-fuchsia-100 text-fuchsia-700", hintClass: "text-fuchsia-700" },
    { title: "Clientes do dia", value: report?.clientes_do_dia ?? 0, hint: "com atendimento hoje", icon: Users, cardClass: "border-sky-200 bg-gradient-to-br from-sky-50 to-white", titleClass: "text-sky-800", iconClass: "bg-sky-100 text-sky-700", hintClass: "text-sky-700" },
    { title: "Total ganho no dia", value: money.format(report?.faturamento ?? 0), hint: "faturamento de hoje", icon: CircleDollarSign, cardClass: "border-emerald-200 bg-gradient-to-br from-emerald-50 to-white", titleClass: "text-emerald-800", iconClass: "bg-emerald-100 text-emerald-700", hintClass: "text-emerald-700" },
    { title: "Pagamentos pendentes", value: pendingPayments.length, hint: money.format(expectedPending), icon: CreditCard, cardClass: "border-amber-200 bg-gradient-to-br from-amber-50 to-white", titleClass: "text-amber-800", iconClass: "bg-amber-100 text-amber-700", hintClass: "text-amber-700" },
  ];

  const comparisons = [
    { label: "Procedimentos", current: report?.agendamentos ?? 0, previous: yesterdayReport?.agendamentos ?? 0 },
    { label: "Clientes", current: report?.clientes_do_dia ?? 0, previous: yesterdayReport?.clientes_do_dia ?? 0 },
    { label: "Faturamento", current: report?.faturamento ?? 0, previous: yesterdayReport?.faturamento ?? 0, currency: true },
  ];

  return <div className="space-y-6">
    <section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm"><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">Mayssa · Dashboard</p><h1 className="mt-2 text-3xl font-semibold text-slate-900">Resumo do dia</h1><p className="mt-2 max-w-3xl text-sm text-slate-500">Agenda, pagamentos e desempenho em uma visão rápida.</p></section>
    {error && <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</div>}

    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{cards.map(({ title, value, hint, icon: Icon, cardClass, titleClass, iconClass, hintClass }) => <div key={title} className={`rounded-2xl border p-5 shadow-sm ${cardClass}`}><div className="flex items-center justify-between"><p className={`text-sm font-medium ${titleClass}`}>{title}</p><span className={`rounded-xl p-2 ${iconClass}`}><Icon size={18} /></span></div><p className="mt-4 text-2xl font-semibold text-slate-900">{value}</p><p className={`mt-2 text-sm font-medium ${hintClass}`}>{hint}</p></div>)}</div>

    <div className="grid gap-4 xl:grid-cols-3">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2"><div className="flex items-center justify-between"><div><h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><CalendarClock size={19} className="text-fuchsia-700" />Próximos atendimentos</h2><p className="mt-1 text-sm text-slate-500">O que ainda está previsto para hoje.</p></div><Link href="/calendario" className="text-sm font-medium text-fuchsia-700">Ver calendário</Link></div>{upcoming.length ? <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[680px] text-left text-sm"><thead className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-400"><tr><th className="px-3 py-2.5">Horário</th><th className="px-3 py-2.5">Cliente</th><th className="px-3 py-2.5">Procedimento</th><th className="px-3 py-2.5">Profissional</th><th className="px-3 py-2.5">Status</th></tr></thead><tbody>{upcoming.map((item) => <tr key={item.id} className="border-b border-slate-100 last:border-0"><td className="px-3 py-3 font-semibold text-slate-900">{item.data_hora.slice(11, 16)}</td><td className="px-3 py-3 text-slate-700">{clientNames.get(item.cliente_id) ?? `Cliente #${item.cliente_id}`}</td><td className="px-3 py-3 text-slate-500">{procedureMap.get(item.procedimento_id)?.nome ?? `Procedimento #${item.procedimento_id}`}</td><td className="px-3 py-3 text-slate-500">{professionalNames.get(item.profissional_id ?? 0) ?? "Sem profissional"}</td><td className="px-3 py-3"><span className={`status-pill status-${item.status}`}>{statusLabels[item.status]?.replace(/s$/, "") ?? item.status}</span></td></tr>)}</tbody></table></div> : <div className="mt-4 rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-400">Nenhum atendimento restante hoje.</div>}</section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Ações rápidas</h2><p className="mt-1 text-sm text-slate-500">Atalhos para as tarefas mais usadas.</p><div className="mt-4 grid grid-cols-2 gap-3">{[
        { href: "/agendamentos", label: "Novo agendamento", icon: CalendarPlus },
        { href: "/clientes", label: "Cadastrar cliente", icon: UserPlus },
        { href: "/calendario", label: "Abrir calendário", icon: CalendarDays },
        { href: "/relatorios", label: "Ver relatórios", icon: ArrowUpRight },
      ].map(({ href, label, icon: Icon }) => <Link key={href + label} href={href} className="flex min-h-24 flex-col justify-between rounded-xl border border-slate-200 p-3 text-sm font-medium text-slate-700 transition hover:border-fuchsia-200 hover:bg-fuchsia-50"><Icon size={20} className="text-fuchsia-700" /><span>{label}</span></Link>)}</div></section>
    </div>

    <div className="grid gap-4 lg:grid-cols-3">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Resumo por status</h2>{statusCounts.length ? <div className="mt-5 flex flex-col items-center gap-5 sm:flex-row lg:flex-col xl:flex-row"><div className="relative h-36 w-36 shrink-0 rounded-full" style={{ background: statusBackground }}><div className="absolute inset-4 flex flex-col items-center justify-center rounded-full bg-white shadow-inner"><strong className="text-2xl text-slate-900">{statusTotal}</strong><span className="text-xs text-slate-400">agendamentos</span></div></div><div className="w-full space-y-2">{statusCounts.map(([status, count]) => <div key={status} className="flex items-center justify-between rounded-lg bg-slate-50 p-2.5 text-sm"><span className="flex items-center gap-2 text-slate-600"><i className="h-3 w-3 rounded-full" style={{ backgroundColor: statusHex[status] ?? "#64748b" }} />{statusLabels[status] ?? status}</span><strong>{count}</strong></div>)}</div></div> : <p className="mt-5 rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">Sem agendamentos hoje.</p>}</section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Comparativo com ontem</h2><div className="mt-4 space-y-3">{comparisons.map((item) => { const change = variation(item.current, item.previous); const ChangeIcon = change >= 0 ? ArrowUpRight : ArrowDownRight; return <div key={item.label} className="flex items-center justify-between rounded-xl bg-slate-50 p-3"><div><p className="text-xs text-slate-400">{item.label}</p><strong className="text-slate-900">{item.currency ? money.format(item.current) : item.current}</strong></div><span className={`flex items-center gap-1 text-xs font-semibold ${change < 0 ? "text-rose-600" : "text-emerald-600"}`}><ChangeIcon size={14} />{Math.abs(change).toFixed(0)}%</span></div>; })}</div></section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><AlertTriangle size={19} className="text-amber-500" />Alertas do dia</h2><div className="mt-4 space-y-3">{[
        { label: "Aguardando confirmação", value: pendingConfirmation },
        { label: "Pagamentos pendentes", value: pendingPayments.length },
        { label: "Sem profissional definido", value: withoutProfessional },
      ].map((alert) => <Link key={alert.label} href="/agendamentos" className="flex items-center justify-between rounded-xl border border-amber-100 bg-amber-50 p-3 text-sm text-amber-900"><span>{alert.label}</span><strong className="flex items-center gap-2">{alert.value}<ArrowRight size={14} /></strong></Link>)}</div></section>
    </div>

    <div className="grid gap-4 xl:grid-cols-2">
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="flex items-center gap-2 text-lg font-semibold text-slate-900"><UserCheck size={19} className="text-fuchsia-700" />Ocupação das profissionais</h2><p className="mt-1 text-sm text-slate-500">Tempo agendado em relação à escala de hoje.</p>{occupancy.length ? <div className="mt-5 flex flex-col items-center gap-5 sm:flex-row lg:flex-col xl:flex-row"><div className="relative h-36 w-36 shrink-0 rounded-full" style={{ background: `conic-gradient(#c026d3 0 ${occupancyPercentage}%, #e2e8f0 ${occupancyPercentage}% 100%)` }}><div className="absolute inset-4 flex flex-col items-center justify-center rounded-full bg-white shadow-inner"><strong className="text-2xl text-slate-900">{occupancyPercentage.toFixed(0)}%</strong><span className="text-xs text-slate-400">ocupação</span></div></div><div className="w-full space-y-2">{occupancy.map((item) => <div key={item.id} className="rounded-lg bg-slate-50 p-2.5"><div className="flex items-center justify-between gap-3 text-sm"><span className="flex min-w-0 items-center gap-2 text-slate-600"><i className="h-3 w-3 shrink-0 rounded-full bg-fuchsia-600" /><span className="truncate">{item.name}</span></span><strong>{item.percentage.toFixed(0)}%</strong></div><p className="mt-1 pl-5 text-xs text-slate-400">{item.count} atendimento(s){item.next ? ` · Próximo às ${item.next.data_hora.slice(11, 16)}` : ""}</p></div>)}</div></div> : <p className="mt-5 rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">Nenhuma profissional ativa.</p>}</section>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Procedimentos mais agendados</h2><p className="mt-1 text-sm text-slate-500">Ranking do mês atual.</p><div className="mt-5 space-y-4">{topProcedures.length ? topProcedures.map((item, index) => <div key={item.id}><div className="mb-1.5 flex justify-between gap-3 text-sm"><span className="truncate text-slate-700"><strong className="mr-2 text-fuchsia-700">{index + 1}º</strong>{procedureMap.get(item.id)?.nome ?? `Procedimento #${item.id}`}</span><strong>{item.count}</strong></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-fuchsia-600" style={{ width: `${(item.count / maximumProcedure) * 100}%` }} /></div></div>) : <p className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">Nenhum procedimento agendado neste mês.</p>}</div></section>
    </div>

    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center justify-between"><div><div className="flex items-center gap-2"><MessageSquareText size={19} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Últimas mensagens recebidas</h2></div><p className="mt-1 text-sm text-slate-500">Contatos recentes do WhatsApp.</p></div><Link href="/conversas" className="text-sm font-medium text-fuchsia-700">Ver conversas</Link></div>{conversations.length ? <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase tracking-wider text-slate-400"><tr><th className="p-3">Contato</th><th className="p-3">Mensagem</th><th className="p-3">Recebida em</th></tr></thead><tbody>{conversations.map((item) => <tr key={item.id} className="border-t border-slate-100"><td className="p-3"><div className="flex items-center gap-3"><ContactAvatar photoUrl={item.foto_perfil} size="small" /><div className="min-w-0"><p className="truncate font-medium text-slate-900">{item.nome_contato || item.telefone}</p><p className="truncate text-xs text-slate-500">{item.telefone}</p></div></div></td><td className="max-w-md truncate p-3 text-slate-600">{item.ultima_mensagem_recebida?.conteudo}</td><td className="whitespace-nowrap p-3 text-slate-500">{item.ultima_mensagem_recebida ? new Date(item.ultima_mensagem_recebida.enviado_em).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"}</td></tr>)}</tbody></table></div> : <div className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">Nenhuma mensagem recebida ainda.</div>}</section>
  </div>;
}
