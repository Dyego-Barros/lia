"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { ChartNoAxesCombined, Coins, Receipt, TrendingUp } from "lucide-react";
import { apiGet } from "@/lib/api";

type Row = { procedimento_id: number; quantidade: number; faturamento: number; custos_materiais: number; lucro: number };
type Report = { inicio: string; fim: string; atendimentos_realizados: number; clientes_do_dia: number; agendamentos: number; faturamento: number; custos_materiais: number; lucro: number; por_procedimento: Row[] };
type Procedure = { id?: number; nome: string };
type AnnualVolume = { ano: number; meses: { mes: number; quantidade: number }[] };

const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const monthNames = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

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
    { label: "Faturamento", value: money.format(report.faturamento), icon: Receipt },
    { label: "Custos de materiais", value: money.format(report.custos_materiais), icon: Coins },
    { label: "Lucro estimado", value: money.format(report.lucro), icon: TrendingUp },
    { label: "Atendimentos", value: report.atendimentos_realizados, icon: ChartNoAxesCombined },
  ] : [];

  return <div className="space-y-6">
    <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Relatório financeiro</p><h1 className="mt-2 text-2xl font-semibold text-slate-900">Faturamento, custos e lucro</h1><p className="mt-2 text-sm text-slate-500">Os custos usam o custo médio de materiais configurado em cada procedimento.</p></header>
    <form onSubmit={load} className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm md:flex-row md:items-end"><label className="flex-1 text-sm text-slate-600">Início<input required className="field mt-1" type="date" value={inicio} max={fim} onChange={(event) => setInicio(event.target.value)} /></label><label className="flex-1 text-sm text-slate-600">Fim<input required className="field mt-1" type="date" value={fim} min={inicio} onChange={(event) => setFim(event.target.value)} /></label><button className="primary-button md:w-auto">Atualizar relatório</button></form>
    {error && <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
    {report && <>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">{cards.map(({ label, value, icon: Icon }) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><p className="text-sm text-slate-500">{label}</p><Icon size={18} className="text-fuchsia-700" /></div><p className="mt-4 text-2xl font-semibold text-slate-900">{value}</p></div>)}</div>
      <div className="grid gap-4 xl:grid-cols-2"><FinancialComposition report={report} />{annualVolume && <MonthlyVolume volume={annualVolume} />}</div>
      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><h2 className="text-lg font-semibold text-slate-900">Resultado por procedimento</h2><p className="mt-1 text-sm text-slate-500">Desempenho financeiro individual no período selecionado.</p>{report.por_procedimento.length ? <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">{report.por_procedimento.map((row) => <article key={row.procedimento_id} className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-50 p-5"><div className="flex items-start justify-between gap-3"><h3 className="font-semibold text-slate-900">{procedureNames.get(row.procedimento_id) ?? `Procedimento #${row.procedimento_id}`}</h3><span className="shrink-0 rounded-full bg-fuchsia-100 px-2.5 py-1 text-xs font-semibold text-fuchsia-700">{row.quantidade} atend.</span></div><div className="mt-5 grid grid-cols-3 gap-2 border-t border-slate-200 pt-4 text-sm"><div><p className="text-xs text-slate-400">Faturamento</p><strong className="mt-1 block text-slate-800">{money.format(row.faturamento)}</strong></div><div><p className="text-xs text-slate-400">Materiais</p><strong className="mt-1 block text-slate-800">{money.format(row.custos_materiais)}</strong></div><div><p className="text-xs text-slate-400">Lucro</p><strong className={`mt-1 block ${row.lucro < 0 ? "text-rose-600" : "text-emerald-700"}`}>{money.format(row.lucro)}</strong></div></div></article>)}</div> : <p className="mt-5 rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">Nenhum atendimento concluído no período.</p>}</section>
    </>}
  </div>;
}
