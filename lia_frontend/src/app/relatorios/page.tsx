"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ChartNoAxesCombined, Coins, Receipt, TrendingUp } from "lucide-react";
import { apiGet } from "@/lib/api";

type Row = { procedimento_id: number; quantidade: number; faturamento: number; custos_materiais: number; lucro: number };
type Report = { inicio: string; fim: string; atendimentos_realizados: number; clientes_do_dia: number; agendamentos: number; faturamento: number; custos_materiais: number; lucro: number; por_procedimento: Row[] };
type Procedure = { id?: number; nome: string };

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

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

function ProcedureVolume({ rows, names }: { rows: Row[]; names: Map<number, string> }) {
  const maximum = Math.max(...rows.map((row) => row.quantidade), 1);

  return <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
    <div><h2 className="text-lg font-semibold text-slate-900">Volume por procedimento</h2><p className="mt-1 text-sm text-slate-500">Quantidade de atendimentos concluídos.</p></div>
    {rows.length ? <div className="mt-6 space-y-4">{rows.map((row) => <div key={row.procedimento_id}>
      <div className="mb-1.5 flex items-center justify-between gap-3 text-sm"><span className="truncate font-medium text-slate-700">{names.get(row.procedimento_id) ?? `Procedimento #${row.procedimento_id}`}</span><strong className="text-slate-900">{row.quantidade}</strong></div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-fuchsia-600 to-emerald-400" style={{ width: `${(row.quantidade / maximum) * 100}%` }} /></div>
    </div>)}</div> : <div className="mt-6 flex h-44 items-center justify-center rounded-xl bg-slate-50 px-6 text-center text-sm text-slate-400">Os volumes aparecerão após a conclusão dos atendimentos.</div>}
  </section>;
}

export default function RelatoriosPage() {
  const period = useMemo(() => currentMonth(), []);
  const [inicio, setInicio] = useState(period.inicio);
  const [fim, setFim] = useState(period.fim);
  const [report, setReport] = useState<Report | null>(null);
  const [procedures, setProcedures] = useState<Procedure[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { if (!error) return; const timer = window.setTimeout(() => setError(null), 5000); return () => window.clearTimeout(timer); }, [error]);
  useEffect(() => { apiGet<Procedure[]>("/procedimentos/").then(setProcedures).catch((reason) => console.error("Falha ao carregar procedimentos", reason)); }, []);

  const load = useCallback(async (event?: FormEvent) => {
    event?.preventDefault();
    try {
      setError(null);
      setReport(await apiGet<Report>(`/relatorios/resumo?inicio=${inicio}&fim=${fim}`));
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
    { label: "Faturamento", value: money.format(report.faturamento), icon: Receipt },
    { label: "Custos de materiais", value: money.format(report.custos_materiais), icon: Coins },
    { label: "Lucro estimado", value: money.format(report.lucro), icon: TrendingUp },
    { label: "Atendimentos", value: report.atendimentos_realizados, icon: ChartNoAxesCombined },
  ] : [];

  return <div className="space-y-6">
    <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Relatório financeiro</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Faturamento, custos e lucro</h1><p className="mt-2 text-sm text-slate-500">Os custos usam o custo médio de materiais configurado em cada procedimento.</p></header>
    <form onSubmit={load} className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-end"><label className="flex-1 text-sm text-slate-600">Início<input className="field mt-1" type="date" value={inicio} max={fim} onChange={(event) => setInicio(event.target.value)} /></label><label className="flex-1 text-sm text-slate-600">Fim<input className="field mt-1" type="date" value={fim} min={inicio} onChange={(event) => setFim(event.target.value)} /></label><button className="primary-button md:w-auto">Atualizar relatório</button></form>
    {error && <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    {report && <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, icon: Icon }) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><p className="text-sm text-slate-500">{label}</p><Icon size={18} className="text-fuchsia-700" /></div><p className="mt-4 text-2xl font-semibold text-slate-900">{value}</p></div>)}</div>
      <div className="grid gap-4 xl:grid-cols-2"><FinancialComposition report={report} /><ProcedureVolume rows={report.por_procedimento} names={procedureNames} /></div>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="mb-4 text-lg font-semibold text-slate-900">Resultado por procedimento</h2><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase tracking-wider text-slate-400"><tr><th className="p-3">Procedimento</th><th className="p-3">Qtd.</th><th className="p-3">Faturamento</th><th className="p-3">Materiais</th><th className="p-3">Lucro</th></tr></thead><tbody>{report.por_procedimento.map((row) => <tr key={row.procedimento_id} className="border-t border-slate-100"><td className="p-3 font-medium text-slate-700">{procedureNames.get(row.procedimento_id) ?? `Procedimento #${row.procedimento_id}`}</td><td className="p-3">{row.quantidade}</td><td className="p-3">{money.format(row.faturamento)}</td><td className="p-3">{money.format(row.custos_materiais)}</td><td className={`p-3 font-semibold ${row.lucro < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money.format(row.lucro)}</td></tr>)}</tbody></table>{!report.por_procedimento.length && <p className="p-6 text-center text-sm text-slate-400">Nenhum atendimento concluído no período.</p>}</div></section>
    </>}
  </div>;
}
