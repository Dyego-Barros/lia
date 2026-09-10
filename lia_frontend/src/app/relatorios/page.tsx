"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ChartNoAxesCombined, Coins, Receipt, TrendingUp } from "lucide-react";
import { apiGet } from "@/lib/api";

type Row = { procedimento_id: number; quantidade: number; faturamento: number; custos_materiais: number; lucro: number };
type DailyPoint = { data: string; faturamento: number; lucro: number };
type PaymentMethod = { forma: string; quantidade: number; valor: number };
type StatusTotal = { status: string; quantidade: number };
type Report = { inicio: string; fim: string; atendimentos_realizados: number; clientes_do_dia: number; agendamentos: number; faturamento: number; custos_materiais: number; lucro: number; por_procedimento: Row[]; por_dia: DailyPoint[]; formas_pagamento: PaymentMethod[]; por_status: StatusTotal[] };
type Procedure = { id?: number; nome: string };
type AnnualVolume = { ano: number; meses: { mes: number; quantidade: number }[] };

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
const chartColors = ["#c026d3", "#10b981", "#6366f1", "#f59e0b", "#0ea5e9", "#f43f5e", "#8b5cf6", "#14b8a6"];
const paymentLabels: Record<string, string> = { pix: "PIX", dinheiro: "Dinheiro", credito: "Cartão de crédito", debito: "Cartão de débito", misto: "Misto", parceria: "Parceria", cortesia: "Cortesia" };
const statusLabels: Record<string, string> = { pendente: "Pendente", confirmado: "Confirmado", cancelado: "Cancelado", concluido: "Concluído", nao_compareceu: "Não compareceu" };
const statusColors: Record<string, string> = { pendente: "#f59e0b", confirmado: "#6366f1", cancelado: "#f43f5e", concluido: "#10b981", nao_compareceu: "#64748b" };

function isoDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function currentMonth() {
  const today = new Date();
  return {
    inicio: isoDate(new Date(today.getFullYear(), today.getMonth(), 1)),
    fim: isoDate(new Date(today.getFullYear(), today.getMonth() + 1, 0)),
  };
}

function FinancialComposition({ report }: { report: Report }) {
  const costs = Math.max(report.custos_materiais, 0);
  const profit = Math.max(report.lucro, 0);
  const total = costs + profit;
  const costPercentage = total ? (costs / total) * 100 : 0;
  const margin = report.faturamento ? (report.lucro / report.faturamento) * 100 : 0;
  const background = total
    ? `conic-gradient(#c026d3 0 ${costPercentage}%, #10b981 ${costPercentage}% 100%)`
    : "conic-gradient(#e2e8f0 0 100%)";

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Composição financeira</h2><p className="mt-1 text-sm text-slate-500">Distribuição entre materiais e lucro no período.</p></div>
    <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row sm:justify-center">
      <div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background }}>
        <div className="absolute inset-5 flex flex-col items-center justify-center rounded-full bg-white text-center shadow-inner"><span className="text-xs uppercase tracking-wide text-slate-400">Margem</span><strong className={`mt-1 text-2xl ${margin < 0 ? "text-rose-600" : "text-slate-900"}`}>{margin.toFixed(1)}%</strong></div>
      </div>
      <div className="w-full max-w-xs space-y-3 text-sm">
        <div className="flex items-center justify-between rounded-xl bg-fuchsia-50 p-3"><span className="flex items-center gap-2 text-slate-600"><i className="h-3 w-3 rounded-full bg-fuchsia-600" />Materiais</span><strong className="text-slate-900">{money.format(report.custos_materiais)}</strong></div>
        <div className="flex items-center justify-between rounded-xl bg-emerald-50 p-3"><span className="flex items-center gap-2 text-slate-600"><i className="h-3 w-3 rounded-full bg-emerald-500" />Lucro</span><strong className={report.lucro < 0 ? "text-rose-600" : "text-slate-900"}>{money.format(report.lucro)}</strong></div>
      </div>
    </div>
  </section>;
}

function MonthlyVolume({ volume }: { volume: AnnualVolume }) {
  const maximum = Math.max(...volume.meses.map((item) => item.quantidade), 1);

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Atendimentos por mês</h2><p className="mt-1 text-sm text-slate-500">Comparativo mensal de atendimentos concluídos em {volume.ano}.</p></div>
    <div className="mt-6 overflow-x-auto pb-1">
      <div className="flex h-60 min-w-[620px] items-end gap-3 border-b border-slate-200 px-2">
        {volume.meses.map((item) => <div key={item.mes} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
          <span className="text-xs font-semibold text-slate-600">{item.quantidade}</span>
          <div className="flex h-44 w-full items-end justify-center"><div className="w-full max-w-9 rounded-t-lg bg-gradient-to-t from-fuchsia-700 to-emerald-400 transition-[height]" style={{ height: item.quantidade ? `${Math.max((item.quantidade / maximum) * 100, 6)}%` : "2px" }} /></div>
          <span className="pb-2 text-xs font-medium text-slate-500">{monthNames[item.mes - 1]}</span>
        </div>)}
      </div>
    </div>
  </section>;
}

function ProcedureComparison({ rows, names }: { rows: Row[]; names: Map<number, string> }) {
  const maximum = Math.max(...rows.flatMap((row) => [row.faturamento, row.custos_materiais, Math.abs(row.lucro)]), 1);

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Desempenho por procedimento</h2><p className="mt-1 text-sm text-slate-500">Comparação entre faturamento, materiais e lucro.</p></div>
    {rows.length ? <div className="mt-6 max-h-96 space-y-6 overflow-y-auto pr-2">{rows.map((row) => <div key={row.procedimento_id}>
      <h3 className="mb-3 truncate text-sm font-semibold text-slate-700">{names.get(row.procedimento_id) ?? `Procedimento #${row.procedimento_id}`}</h3>
      {[
        { label: "Faturamento", value: row.faturamento, color: "bg-indigo-500" },
        { label: "Materiais", value: row.custos_materiais, color: "bg-fuchsia-600" },
        { label: "Lucro", value: row.lucro, color: row.lucro < 0 ? "bg-rose-500" : "bg-emerald-500" },
      ].map((item) => <div key={item.label} className="mb-2 grid grid-cols-[76px_1fr_96px] items-center gap-2 text-xs"><span className="text-slate-500">{item.label}</span><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${item.color}`} style={{ width: `${(Math.abs(item.value) / maximum) * 100}%` }} /></div><strong className="text-right text-slate-700">{money.format(item.value)}</strong></div>)}
    </div>)}</div> : <div className="mt-6 flex h-52 items-center justify-center rounded-xl bg-slate-50 px-6 text-center text-sm text-slate-400">Os dados aparecerão após a conclusão dos atendimentos.</div>}
  </section>;
}

function MaterialConsumptionByProcedure({ rows, names }: { rows: Row[]; names: Map<number, string> }) {
  const consumption = [...rows]
    .filter((row) => row.custos_materiais > 0)
    .sort((first, second) => second.custos_materiais - first.custos_materiais);
  const maximum = Math.max(...consumption.map((row) => row.custos_materiais), 1);

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
    <div>
      <h2 className="text-lg font-semibold text-slate-900">Consumo de materiais por procedimento</h2>
      <p className="mt-1 text-sm text-slate-500">Procedimentos ordenados pelo maior valor consumido em materiais no período.</p>
    </div>
    {consumption.length ? <div className="mt-6 overflow-x-auto pb-1">
      <div className="flex h-72 min-w-max items-end gap-4 border-b border-slate-200 px-3" role="img" aria-label="Gráfico de colunas do valor consumido em materiais por procedimento">
        {consumption.map((row) => {
          const procedureName = names.get(row.procedimento_id) ?? `Procedimento #${row.procedimento_id}`;
          return <div key={row.procedimento_id} className="flex h-full w-28 shrink-0 flex-col items-center justify-end gap-2">
            <strong className="text-xs text-slate-700">{money.format(row.custos_materiais)}</strong>
            <div className="flex h-44 w-full items-end justify-center">
              <div
                className="w-14 rounded-t-xl bg-gradient-to-t from-fuchsia-700 to-fuchsia-400 shadow-sm transition-[height]"
                style={{ height: `${Math.max((row.custos_materiais / maximum) * 100, 4)}%` }}
                title={`${procedureName}: ${money.format(row.custos_materiais)}`}
              />
            </div>
            <span className="flex h-12 items-start justify-center overflow-hidden pb-2 text-center text-xs font-medium leading-4 text-slate-600" title={procedureName}>{procedureName}</span>
          </div>;
        })}
      </div>
    </div> : <div className="mt-6 flex h-52 items-center justify-center rounded-xl bg-slate-50 px-6 text-center text-sm text-slate-400">Nenhum consumo de materiais registrado no período.</div>}
  </section>;
}

function RevenueShare({ rows, names }: { rows: Row[]; names: Map<number, string> }) {
  const total = rows.reduce((sum, row) => sum + Math.max(row.faturamento, 0), 0);
  let cursor = 0;
  const segments = rows.map((row, index) => {
    const start = cursor;
    cursor += total ? (Math.max(row.faturamento, 0) / total) * 100 : 0;
    return `${chartColors[index % chartColors.length]} ${start}% ${cursor}%`;
  });
  const background = total ? `conic-gradient(${segments.join(", ")})` : "conic-gradient(#e2e8f0 0 100%)";

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Participação no faturamento</h2><p className="mt-1 text-sm text-slate-500">Quanto cada procedimento representa no total.</p></div>
    <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row sm:justify-center">
      <div className="relative h-44 w-44 shrink-0 rounded-full" style={{ background }}><div className="absolute inset-5 flex flex-col items-center justify-center rounded-full bg-white text-center shadow-inner"><span className="text-xs uppercase tracking-wide text-slate-400">Total</span><strong className="mt-1 text-lg text-slate-900">{money.format(total)}</strong></div></div>
      {rows.length ? <div className="max-h-52 w-full max-w-sm space-y-2 overflow-y-auto pr-1 text-sm">{rows.map((row, index) => <div key={row.procedimento_id} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 p-2.5"><span className="flex min-w-0 items-center gap-2 text-slate-600"><i className="h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} /><span className="truncate">{names.get(row.procedimento_id) ?? `Procedimento #${row.procedimento_id}`}</span></span><strong className="shrink-0 text-slate-800">{total ? ((row.faturamento / total) * 100).toFixed(1) : "0.0"}%</strong></div>)}</div> : <p className="text-sm text-slate-400">Sem faturamento no período.</p>}
    </div>
  </section>;
}

function DailyFinancialTrend({ data }: { data: DailyPoint[] }) {
  const width = 760;
  const height = 250;
  const left = 58;
  const right = 18;
  const top = 18;
  const bottom = 34;
  const chartWidth = width - left - right;
  const chartHeight = height - top - bottom;
  const maximum = Math.max(...data.flatMap((item) => [item.faturamento, item.lucro]), 1);
  const x = (index: number) => left + (index / Math.max(data.length - 1, 1)) * chartWidth;
  const y = (value: number) => top + chartHeight - (Math.max(value, 0) / maximum) * chartHeight;
  const points = (field: "faturamento" | "lucro") => data.map((item, index) => `${x(index)},${y(item[field])}`).join(" ");
  const labels = data.length ? [data[0], data[Math.floor((data.length - 1) / 2)], data[data.length - 1]] : [];

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-2">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between"><div><h2 className="text-lg font-semibold text-slate-900">Evolução financeira diária</h2><p className="mt-1 text-sm text-slate-500">Faturamento e lucro ao longo do período selecionado.</p></div><div className="flex gap-4 text-xs text-slate-500"><span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-full bg-indigo-500" />Faturamento</span><span className="flex items-center gap-2"><i className="h-2.5 w-2.5 rounded-full bg-emerald-500" />Lucro</span></div></div>
    <div className="mt-4 overflow-x-auto"><svg role="img" aria-label="Evolução diária de faturamento e lucro" viewBox={`0 0 ${width} ${height}`} className="mx-auto block h-auto w-full min-w-[680px] max-w-[1000px]">
      {[0, 0.25, 0.5, 0.75, 1].map((ratio) => { const position = top + chartHeight - ratio * chartHeight; return <g key={ratio}><line x1={left} x2={width - right} y1={position} y2={position} stroke="#e2e8f0" strokeWidth="1" /><text x={left - 8} y={position + 4} textAnchor="end" fontSize="10" fill="#94a3b8">{money.format(maximum * ratio).replace(",00", "")}</text></g>; })}
      <polyline points={points("faturamento")} fill="none" stroke="#6366f1" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      <polyline points={points("lucro")} fill="none" stroke="#10b981" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
      {labels.map((item, index) => <text key={`${item.data}-${index}`} x={x(index === 0 ? 0 : index === 1 ? Math.floor((data.length - 1) / 2) : data.length - 1)} y={height - 8} textAnchor={index === 0 ? "start" : index === 2 ? "end" : "middle"} fontSize="11" fill="#64748b">{item.data.slice(8, 10)}/{item.data.slice(5, 7)}</text>)}
    </svg></div>
  </section>;
}

function PaymentMethodsChart({ items }: { items: PaymentMethod[] }) {
  const total = items.reduce((sum, item) => sum + item.quantidade, 0);
  const totalValue = items.reduce((sum, item) => sum + item.valor, 0);
  const maximumValue = Math.max(...items.map((item) => item.valor), 1);
  let cursor = 0;
  const segments = items.map((item, index) => {
    const start = cursor;
    cursor += total ? (item.quantidade / total) * 100 : 0;
    return `${chartColors[index % chartColors.length]} ${start}% ${cursor}%`;
  });
  const background = total ? `conic-gradient(${segments.join(", ")})` : "conic-gradient(#e2e8f0 0 100%)";

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Formas de pagamento</h2><p className="mt-1 text-sm text-slate-500">Distribuição dos pagamentos confirmados.</p></div>
    <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row sm:justify-center"><div className="relative h-40 w-40 shrink-0 rounded-full" style={{ background }}><div className="absolute inset-5 flex flex-col items-center justify-center rounded-full bg-white text-center shadow-inner"><strong className="text-xl text-slate-900">{money.format(totalValue)}</strong><span className="text-xs text-slate-400">{total} pagamentos</span></div></div>{items.length ? <div className="w-full max-w-sm space-y-2 text-sm">{items.map((item, index) => <div key={item.forma} className="flex items-center justify-between rounded-lg bg-slate-50 p-2.5"><span className="flex items-center gap-2 text-slate-600"><i className="h-3 w-3 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} />{paymentLabels[item.forma] ?? item.forma}</span><strong className="text-slate-800">{item.quantidade}</strong></div>)}</div> : <p className="text-sm text-slate-400">Nenhum pagamento confirmado.</p>}</div>
    {items.length > 0 && <div className="mt-6 border-t border-slate-100 pt-5"><h3 className="mb-4 text-sm font-semibold text-slate-700">Valor arrecadado por forma</h3><div className="space-y-3">{items.map((item, index) => <div key={`valor-${item.forma}`}><div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="text-slate-500">{paymentLabels[item.forma] ?? item.forma}</span><strong className="text-slate-800">{money.format(item.valor)}</strong></div><div className="h-3 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full" style={{ width: `${(item.valor / maximumValue) * 100}%`, backgroundColor: chartColors[index % chartColors.length] }} /></div></div>)}</div></div>}
  </section>;
}

function AppointmentStatusChart({ items }: { items: StatusTotal[] }) {
  const total = items.reduce((sum, item) => sum + item.quantidade, 0);
  let cursor = 0;
  const segments = items.map((item) => {
    const start = cursor;
    cursor += total ? (item.quantidade / total) * 100 : 0;
    return `${statusColors[item.status] ?? "#64748b"} ${start}% ${cursor}%`;
  });
  const background = total ? `conic-gradient(${segments.join(", ")})` : "conic-gradient(#e2e8f0 0 100%)";

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Status dos atendimentos</h2><p className="mt-1 text-sm text-slate-500">Situação dos {total} agendamentos no período.</p></div>
    {items.length ? <div className="mt-6 flex flex-col items-center gap-6 sm:flex-row sm:justify-center"><div className="relative h-40 w-40 shrink-0 rounded-full" style={{ background }}><div className="absolute inset-5 flex flex-col items-center justify-center rounded-full bg-white text-center shadow-inner"><strong className="text-2xl text-slate-900">{total}</strong><span className="text-xs text-slate-400">agendamentos</span></div></div><div className="w-full max-w-sm space-y-2 text-sm">{items.map((item) => <div key={item.status} className="flex items-center justify-between rounded-lg bg-slate-50 p-2.5"><span className="flex items-center gap-2 text-slate-600"><i className="h-3 w-3 rounded-full" style={{ backgroundColor: statusColors[item.status] ?? "#64748b" }} />{statusLabels[item.status] ?? item.status}</span><strong className="text-slate-800">{item.quantidade}</strong></div>)}</div></div> : <div className="mt-6 flex h-40 items-center justify-center rounded-xl bg-slate-50 text-sm text-slate-400">Nenhum agendamento no período.</div>}
  </section>;
}

export default function RelatoriosPage() {
  const period = useMemo(() => currentMonth(), []);
  const [inicio, setInicio] = useState(period.inicio);
  const [fim, setFim] = useState(period.fim);
  const [report, setReport] = useState<Report | null>(null);
  const [annualVolume, setAnnualVolume] = useState<AnnualVolume | null>(null);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { if (!error) return; const timer = window.setTimeout(() => setError(null), 5000); return () => window.clearTimeout(timer); }, [error]);
  useEffect(() => { apiGet<Procedure[]>("/procedimentos/").then(setProcedures).catch((reason) => console.error("Falha ao carregar procedimentos", reason)); }, []);

  const load = useCallback(async (event?: FormEvent) => {
    event?.preventDefault();
    try {
      setError(null);
      const year = Number(fim.slice(0, 4));
      const [nextReport, nextAnnualVolume] = await Promise.all([
        apiGet<Report>(`/relatorios/resumo?inicio=${inicio}&fim=${fim}`),
        apiGet<AnnualVolume>(`/relatorios/volume-anual?ano=${year}`),
      ]);
      setReport(nextReport);
      setAnnualVolume(nextAnnualVolume);
    } catch (reason) {
      if (event) setError(reason instanceof Error ? reason.message : "Não foi possível carregar o relatório.");
      else console.error("Falha ao carregar o relatório", reason);
    }
  }, [fim, inicio]);

  // O primeiro carregamento precisa sincronizar os dados externos ao montar a página.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { void load(); }, [load]);

  const procedureNames = useMemo(() => new Map(procedures.flatMap((procedure) => procedure.id ? [[procedure.id, procedure.nome] as const] : [])), [procedures]);
  const cards = report ? [
    { label: "Faturamento", value: money.format(report.faturamento), icon: Receipt, cardClass: "border-fuchsia-200 bg-gradient-to-br from-fuchsia-50 to-white", labelClass: "text-fuchsia-800", iconClass: "bg-fuchsia-100 text-fuchsia-700" },
    { label: "Custos de materiais", value: money.format(report.custos_materiais), icon: Coins, cardClass: "border-sky-200 bg-gradient-to-br from-sky-50 to-white", labelClass: "text-sky-800", iconClass: "bg-sky-100 text-sky-700" },
    { label: "Lucro estimado", value: money.format(report.lucro), icon: TrendingUp, cardClass: "border-emerald-200 bg-gradient-to-br from-emerald-50 to-white", labelClass: "text-emerald-800", iconClass: "bg-emerald-100 text-emerald-700" },
    { label: "Atendimentos", value: report.atendimentos_realizados, icon: ChartNoAxesCombined, cardClass: "border-amber-200 bg-gradient-to-br from-amber-50 to-white", labelClass: "text-amber-800", iconClass: "bg-amber-100 text-amber-700" },
  ] : [];

  return <div className="space-y-6">
    <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">Mayssa · Relatório financeiro</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Faturamento, custos e lucro</h1><p className="mt-2 text-sm text-slate-500">Os custos usam o custo médio de materiais configurado em cada procedimento.</p></header>
    <form onSubmit={load} className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-end"><label className="flex-1 text-sm text-slate-600">Início<input required className="field mt-1" type="date" value={inicio} max={fim} onChange={(event) => setInicio(event.target.value)} /></label><label className="flex-1 text-sm text-slate-600">Fim<input required className="field mt-1" type="date" value={fim} min={inicio} onChange={(event) => setFim(event.target.value)} /></label><button className="primary-button md:w-auto">Atualizar relatório</button></form>
    {error && <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    {report && <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, icon: Icon, cardClass, labelClass, iconClass }) => <div key={label} className={`rounded-2xl border p-5 shadow-sm ${cardClass}`}><div className="flex items-center justify-between"><p className={`text-sm font-medium ${labelClass}`}>{label}</p><span className={`rounded-xl p-2 ${iconClass}`}><Icon size={18} /></span></div><p className="mt-4 text-2xl font-semibold text-slate-900">{value}</p></div>)}</div>
      <div className="grid gap-4 xl:grid-cols-2"><FinancialComposition report={report} />{annualVolume && <MonthlyVolume volume={annualVolume} />}</div>
      <div className="grid gap-4 xl:grid-cols-2"><MaterialConsumptionByProcedure rows={report.por_procedimento} names={procedureNames} /></div>
      <div className="grid gap-4 xl:grid-cols-2"><DailyFinancialTrend data={report.por_dia} /><PaymentMethodsChart items={report.formas_pagamento} /><AppointmentStatusChart items={report.por_status} /></div>
      <div className="grid gap-4 xl:grid-cols-2"><ProcedureComparison rows={report.por_procedimento} names={procedureNames} /><RevenueShare rows={report.por_procedimento} names={procedureNames} /></div>
    </>}
  </div>;
}
