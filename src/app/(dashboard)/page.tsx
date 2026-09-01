"use client";

import { useEffect, useState } from "react";
import { Activity, CircleDollarSign, MessageSquareText, Users } from "lucide-react";
import { apiGet } from "@/lib/api";
import { ContactAvatar } from "@/components/contact-avatar";

type DailyReport = { atendimentos_realizados: number; clientes_do_dia: number; faturamento: number };
type Conversation = { id: string; telefone: string; nome_contato: string | null; foto_perfil?: string | null; ultima_mensagem_recebida?: { conteudo: string; enviado_em: string } | null };
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function today() {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

export default function DashboardPage() {
  const [report, setReport] = useState<DailyReport | null>(null); const [conversations, setConversations] = useState<Conversation[]>([]);
  const [error] = useState<string | null>(null);

  useEffect(() => {
    const date = today();
    Promise.allSettled([apiGet<DailyReport>(`/relatorios/resumo?inicio=${date}&fim=${date}`), apiGet<Conversation[]>("/integracoes/conversas")]).then(([daily, inbox]) => {
      if (daily.status === "fulfilled") setReport(daily.value); else console.error("Falha ao carregar o dashboard", daily.reason);
      if (inbox.status === "fulfilled") setConversations(inbox.value.filter((item) => item.ultima_mensagem_recebida).slice(0, 8));
    });
  }, []);

  const cards = [
    { title: "Procedimentos do dia", value: report?.atendimentos_realizados ?? 0, hint: "realizados hoje", icon: Activity },
    { title: "Clientes do dia", value: report?.clientes_do_dia ?? 0, hint: "com atendimento hoje", icon: Users },
    { title: "Total ganho no dia", value: report ? money.format(report.faturamento) : money.format(0), hint: "faturamento de hoje", icon: CircleDollarSign },
  ];

  return <div className="space-y-6"><section className="rounded-2xl border border-slate-200 bg-white p-7 shadow-sm"><p className="text-sm font-medium uppercase tracking-[0.25em] text-fuchsia-700">MAYA · Dashboard</p><h1 className="mt-2 text-3xl font-semibold text-slate-900">Resumo do dia</h1><p className="mt-2 max-w-3xl text-sm text-slate-500">Acompanhe os principais resultados e as conversas recentes com seus clientes.</p></section>{error && <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700">{error}</div>}<div className="grid gap-4 md:grid-cols-3">{cards.map(({ title, value, hint, icon: Icon }) => <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><p className="text-sm text-slate-500">{title}</p><span className="rounded-xl bg-fuchsia-50 p-2 text-fuchsia-700"><Icon size={18} /></span></div><p className="mt-4 text-2xl font-semibold text-slate-900">{value}</p><p className="mt-2 text-sm text-fuchsia-700">{hint}</p></div>)}</div><section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="mb-4 flex items-center justify-between"><div><div className="flex items-center gap-2"><MessageSquareText size={19} className="text-fuchsia-700" /><h2 className="text-lg font-semibold text-slate-900">Últimas mensagens recebidas</h2></div><p className="mt-1 text-sm text-slate-500">Acompanhe rapidamente os contatos mais recentes do WhatsApp.</p></div><a href="/conversas" className="text-sm font-medium text-fuchsia-700 hover:text-fuchsia-900">Ver conversas</a></div>{conversations.length ? <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase tracking-wider text-slate-400"><tr><th className="p-3">Contato</th><th className="p-3">Mensagem</th><th className="p-3">Recebida em</th></tr></thead><tbody>{conversations.map((item) => <tr key={item.id} className="border-t border-slate-100"><td className="p-3"><div className="flex items-center gap-3"><ContactAvatar photoUrl={item.foto_perfil} size="small" /><div className="min-w-0"><p className="truncate font-medium text-slate-900">{item.nome_contato || item.telefone}</p><p className="truncate text-xs text-slate-500">{item.telefone}</p></div></div></td><td className="max-w-md truncate p-3 text-slate-600">{item.ultima_mensagem_recebida?.conteudo}</td><td className="whitespace-nowrap p-3 text-slate-500">{item.ultima_mensagem_recebida ? new Date(item.ultima_mensagem_recebida.enviado_em).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : "—"}</td></tr>)}</tbody></table></div> : <div className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-400">Nenhuma mensagem recebida ainda.</div>}</section></div>;
}
