"use client";

import { useEffect, useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight } from "lucide-react";
import { apiGet } from "@/lib/api";

type Appointment = { id?: number; cliente_id: number; procedimento_id: number; data_hora: string; status: string };
type Client = { id?: number; nome: string };
type Procedure = { id?: number; nome: string };

const weekdays = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];
const monthFormatter = new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric" });

function dateKey(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function startOfMonth(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function startOfCalendar(date: Date) {
  const first = startOfMonth(date);
  const day = first.getDay();
  first.setDate(first.getDate() - (day === 0 ? 6 : day - 1));
  first.setHours(0, 0, 0, 0);
  return first;
}

function endOfCalendar(date: Date) {
  const last = new Date(date.getFullYear(), date.getMonth() + 1, 0);
  const day = last.getDay();
  last.setDate(last.getDate() + (day === 0 ? 0 : 7 - day));
  last.setHours(0, 0, 0, 0);
  return last;
}

export default function CalendarioPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [month, setMonth] = useState(() => startOfMonth(new Date()));

  useEffect(() => {
    Promise.all([apiGet<Appointment[]>("/agendamentos/"), apiGet<Client[]>("/clientes/"), apiGet<Procedure[]>("/procedimentos/")])
      .then(([a, c, p]) => { setAppointments(a); setClients(c); setProcedures(p); });
  }, []);

  const days = useMemo(() => {
    const first = startOfCalendar(month);
    const last = endOfCalendar(month);
    const result: Date[] = [];
    for (const cursor = new Date(first); cursor <= last; cursor.setDate(cursor.getDate() + 1)) result.push(new Date(cursor));
    return result;
  }, [month]);

  function moveMonth(amount: number) {
    setMonth((current) => new Date(current.getFullYear(), current.getMonth() + amount, 1));
  }

  function goToday() {
    setMonth(startOfMonth(new Date()));
  }

  const todayKey = dateKey(new Date());
  const title = monthFormatter.format(month).replace(/^./, (letter) => letter.toUpperCase());

  return <div className="space-y-6"><header className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><div><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Calendário</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Agenda mensal</h1><p className="mt-2 text-sm text-slate-500">Visualize todos os agendamentos do mês e navegue entre os períodos.</p></div><CalendarDays className="text-fuchsia-700" size={28} /></header><section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:p-5"><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><button onClick={() => moveMonth(-1)} aria-label="Mês anterior" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><ChevronLeft /></button><button onClick={goToday} className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">Hoje</button><button onClick={() => moveMonth(1)} aria-label="Próximo mês" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><ChevronRight /></button></div><p className="text-lg font-semibold text-slate-900">{title}</p><p className="text-sm text-slate-500">{appointments.filter((item) => new Date(item.data_hora).getMonth() === month.getMonth() && new Date(item.data_hora).getFullYear() === month.getFullYear()).length} agendamentos</p></div><div className="overflow-x-auto"><div className="min-w-[900px]"><div className="grid grid-cols-7 gap-px overflow-hidden rounded-t-xl border border-slate-200 bg-slate-200">{weekdays.map((day) => <div key={day} className="bg-slate-50 p-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-500">{day}</div>)}</div><div className="grid grid-cols-7 gap-px overflow-hidden rounded-b-xl border-x border-b border-slate-200 bg-slate-200">{days.map((date) => { const key = dateKey(date); const items = appointments.filter((item) => dateKey(new Date(item.data_hora)) === key); const outside = date.getMonth() !== month.getMonth(); return <div key={key} className={`min-h-36 bg-white p-2 ${outside ? "bg-slate-50/70" : ""}`}><div className="flex items-center justify-between"><span className={`inline-flex h-7 w-7 items-center justify-center rounded-full text-sm font-semibold ${key === todayKey ? "bg-fuchsia-700 text-white" : outside ? "text-slate-300" : "text-slate-700"}`}>{date.getDate()}</span>{items.length > 0 && <span className="text-[11px] font-medium text-slate-400">{items.length}</span>}</div><div className="mt-2 space-y-1.5">{items.map((item) => <div key={item.id} className={`rounded-lg border p-2 text-xs shadow-sm ${item.status === "cancelado" ? "border-rose-100 bg-rose-50/60" : "border-fuchsia-100 bg-fuchsia-50/70"}`}><p className="font-semibold text-slate-800">{new Date(item.data_hora).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</p><p className="truncate text-slate-600">{clients.find((client) => client.id === item.cliente_id)?.nome ?? `Cliente #${item.cliente_id}`}</p><p className="truncate text-fuchsia-700">{procedures.find((procedure) => procedure.id === item.procedimento_id)?.nome ?? `Procedimento #${item.procedimento_id}`}</p></div>)}</div></div>; })}</div></div></div></section></div>;
}
